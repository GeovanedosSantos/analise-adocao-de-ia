import random

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import F

from apps.contas.tenancy import ignorar_rls

from . import llm
from .models import Avaliacao, Resposta, StatusAvaliacao


def espera_para_retentativa(tentativa):
    """Backoff exponencial com jitter: ~5s, ~25s, ~125s."""
    return 5 ** (tentativa + 1) + random.uniform(0, 1)


@shared_task(bind=True)
def processar_respostas_abertas(self, avaliacao_id):
    """Analisa as respostas abertas com o LLM local (RF08-RF10, US04).

    Cada análise válida é salva na hora, então uma retentativa só reenvia o que falhou.
    """
    try:
        pendentes = _pendentes(avaliacao_id)
        for resposta in pendentes:
            analise = llm.analisar_resposta(resposta.pergunta.texto, resposta.texto_aberto)
            _salvar_analise(resposta, analise)
    except llm.FalhaInferencia as exc:
        _registrar_tentativa(avaliacao_id)
        if self.request.retries >= settings.IA_MAX_TENTATIVAS:
            _atualizar_status(avaliacao_id, StatusAvaliacao.ERRO_PROCESSAMENTO)
            return
        raise self.retry(exc=exc, countdown=espera_para_retentativa(self.request.retries), max_retries=None)
    _atualizar_status(avaliacao_id, StatusAvaliacao.CONCLUIDA)


def _pendentes_qs(avaliacao_id):
    return Resposta.objects.filter(avaliacao_id=avaliacao_id, feedback_ia__isnull=True).exclude(texto_aberto='')


def _pendentes(avaliacao_id):
    with transaction.atomic(), ignorar_rls():
        return list(_pendentes_qs(avaliacao_id).select_related('pergunta'))


def _salvar_analise(resposta, analise):
    with transaction.atomic(), ignorar_rls():
        Resposta.objects.filter(pk=resposta.pk).update(feedback_ia=analise)


def _registrar_tentativa(avaliacao_id):
    with transaction.atomic(), ignorar_rls():
        _pendentes_qs(avaliacao_id).update(tentativas_ia=F('tentativas_ia') + 1)


def _atualizar_status(avaliacao_id, status):
    with transaction.atomic(), ignorar_rls():
        Avaliacao.objects.filter(pk=avaliacao_id).update(status=status)
