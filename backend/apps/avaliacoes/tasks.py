import random

from celery import shared_task
from django.conf import settings
from django.db.models import F

from apps.contas.tenancy import transacao_da_empresa

from . import llm
from .models import Avaliacao, Resposta, StatusAvaliacao


def espera_para_retentativa(tentativa):
    """Backoff exponencial com jitter: ~5s, ~25s, ~125s."""
    return 5 ** (tentativa + 1) + random.uniform(0, 1)


@shared_task(bind=True)
def processar_ia(self, avaliacao_id, empresa_id):
    """Trabalho do LLM local depois da submissão (UC12).

    1. Analisa as respostas abertas (RF08, US05).
    2. Ranqueia as recomendações aplicáveis a partir das notas, dos pesos e dessa análise, e grava as
       TOTAL_RECOMENDACOES primeiras.

    Todo acesso ao banco roda com o tenant da avaliação, então as políticas de RLS continuam valendo.
    Cada etapa concluída é salva na hora, e uma retentativa só refaz o que falhou. Se as tentativas
    acabarem, o status vira ERRO_PROCESSAMENTO e o plano de ação fica na ordem das faixas (UC12 E02).
    """
    from . import services  # services importa este módulo

    try:
        for resposta in _pendentes(avaliacao_id, empresa_id):
            analise = llm.analisar_resposta(resposta.pergunta.texto, resposta.texto_aberto)
            _salvar_analise(resposta, analise, empresa_id)
        _ranquear_recomendacoes(avaliacao_id, empresa_id, services)
    except llm.FalhaInferencia as exc:
        _registrar_tentativa(avaliacao_id, empresa_id)
        if self.request.retries >= settings.IA_MAX_TENTATIVAS:
            _atualizar_status(avaliacao_id, empresa_id, StatusAvaliacao.ERRO_PROCESSAMENTO)
            return
        raise self.retry(exc=exc, countdown=espera_para_retentativa(self.request.retries), max_retries=None)
    _atualizar_status(avaliacao_id, empresa_id, StatusAvaliacao.CONCLUIDA)


def _pendentes_qs(avaliacao_id):
    return Resposta.objects.filter(avaliacao_id=avaliacao_id, feedback_ia__isnull=True).exclude(texto_aberto='')


def _pendentes(avaliacao_id, empresa_id):
    with transacao_da_empresa(empresa_id):
        return list(_pendentes_qs(avaliacao_id).select_related('pergunta'))


def _salvar_analise(resposta, analise, empresa_id):
    with transacao_da_empresa(empresa_id):
        Resposta.objects.filter(pk=resposta.pk).update(feedback_ia=analise)


def _ranquear_recomendacoes(avaliacao_id, empresa_id, services):
    with transacao_da_empresa(empresa_id):
        avaliacao = Avaliacao.objects.get(pk=avaliacao_id)
        if avaliacao.recomendacoes_ordenadas_ia:
            return
        candidatas = services.recomendacoes_aplicaveis(avaliacao)[:settings.IA_MAX_CANDIDATAS]
        dimensoes = {
            p.dimensao.codigo: {'nota': p.nota, 'peso': p.dimensao.peso}
            for p in avaliacao.pontuacoes.select_related('dimensao')
        }
        analises = [
            {
                'dimensao': r.pergunta.dimensao.codigo,
                'analise': r.feedback_ia['analise_qualitativa'],
                'riscos': r.feedback_ia['riscos'],
            }
            for r in avaliacao.respostas.filter(feedback_ia__isnull=False).select_related('pergunta__dimensao')
        ]
    if len(candidatas) < 2:
        return
    acoes = [
        {
            'codigo': r.codigo, 'dimensao': r.dimensao_codigo, 'titulo': r.titulo, 'prioridade': r.prioridade,
            'impacto': r.impacto, 'esforco': r.esforco, 'prazo': r.prazo,
        }
        for _, r in candidatas
    ]
    # Fora da transação: a inferência pode levar dezenas de segundos
    ranking = llm.ordenar_recomendacoes(avaliacao.nota_geral, dimensoes, acoes, analises)
    with transacao_da_empresa(empresa_id):
        services.selecionar_recomendacoes(avaliacao, ranking=ranking)
        Avaliacao.objects.filter(pk=avaliacao_id).update(
            recomendacoes_ordenadas_ia=True, versao_prompts_ia=llm.VERSAO_PROMPTS,
        )


def _registrar_tentativa(avaliacao_id, empresa_id):
    with transacao_da_empresa(empresa_id):
        _pendentes_qs(avaliacao_id).update(tentativas_ia=F('tentativas_ia') + 1)


def _atualizar_status(avaliacao_id, empresa_id, status):
    with transacao_da_empresa(empresa_id):
        Avaliacao.objects.filter(pk=avaliacao_id).update(status=status)
