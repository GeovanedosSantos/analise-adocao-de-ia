from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.questionarios.models import Pergunta, Questionario, TipoPergunta

from .models import ESCALA_MAX, ESCALA_MIN, Avaliacao, PontuacaoDimensao, Resposta, StatusAvaliacao
from .tasks import processar_respostas_abertas


class AvaliacaoJaSubmetida(APIException):
    status_code = 409
    default_detail = 'A avaliação já foi submetida e não pode mais ser alterada.'
    default_code = 'avaliacao_ja_submetida'


def iniciar_avaliacao(empresa):
    """Retoma o rascunho da empresa ou abre um novo na versão ativa. Retorna (avaliacao, criada)."""
    rascunho = Avaliacao.objects.filter(empresa=empresa, status=StatusAvaliacao.RASCUNHO).first()
    if rascunho:
        return rascunho, False
    questionario = Questionario.objects.get(ativo=True)
    # get_or_create cobre duas requisições simultâneas: a que perde a corrida busca o rascunho criado
    return Avaliacao.objects.get_or_create(
        empresa=empresa, status=StatusAvaliacao.RASCUNHO, defaults={'questionario': questionario},
    )


def salvar_rascunho(avaliacao, itens):
    """Grava as respostas parciais (RF04). `itens` já validados: pergunta + campos enviados."""
    _exigir_rascunho(avaliacao)
    for item in itens:
        campos = {c: item[c] for c in ('valor_objetivo', 'texto_aberto') if c in item}
        Resposta.objects.update_or_create(avaliacao=avaliacao, pergunta=item['pergunta'], defaults=campos)


def submeter(avaliacao):
    """Fecha a avaliação, calcula a nota e, se houver respostas abertas, enfileira a análise da IA."""
    _exigir_rascunho(avaliacao)
    faltantes = _objetivas_sem_resposta(avaliacao)
    if faltantes:
        raise ValidationError({'perguntas_sem_resposta': [str(p.id) for p in faltantes]})

    calcular_pontuacao(avaliacao)
    tem_abertas = avaliacao.respostas.exclude(texto_aberto='').exists()
    avaliacao.status = StatusAvaliacao.PROCESSANDO_IA if tem_abertas else StatusAvaliacao.CONCLUIDA
    avaliacao.data_fim = timezone.now()
    avaliacao.save(update_fields=['status', 'data_fim'])
    if tem_abertas:
        transaction.on_commit(lambda: processar_respostas_abertas.delay(str(avaliacao.id)))
    return avaliacao


@transaction.atomic
def calcular_pontuacao(avaliacao):
    """Motor determinístico (RF05, RF06, RF07).

    - Nota da dimensão: média das objetivas ponderada pelo peso da pergunta, levada de 0 a 100.
    - Nota geral: média das dimensões ponderada pelo peso da dimensão.
    - Dimensão prioritária: a de menor nota.
    """
    valores = dict(avaliacao.respostas.filter(valor_objetivo__isnull=False).values_list('pergunta_id', 'valor_objetivo'))
    por_dimensao = defaultdict(list)
    for pergunta in _objetivas_ativas(avaliacao).select_related('dimensao'):
        if pergunta.id in valores:
            por_dimensao[pergunta.dimensao].append((pergunta.peso, valores[pergunta.id]))

    pontuacoes = [
        PontuacaoDimensao(avaliacao=avaliacao, dimensao=dimensao, nota=_nota_normalizada(itens))
        for dimensao, itens in sorted(por_dimensao.items(), key=lambda par: par[0].ordem)
    ]
    if pontuacoes:
        min(pontuacoes, key=lambda p: p.nota).prioritaria = True
    avaliacao.pontuacoes.all().delete()
    PontuacaoDimensao.objects.bulk_create(pontuacoes)

    peso_total = sum(p.dimensao.peso for p in pontuacoes)
    avaliacao.nota_geral = sum(p.nota * p.dimensao.peso for p in pontuacoes) / peso_total if peso_total else None
    avaliacao.nivel_maturidade = _nivel(avaliacao.nota_geral)
    avaliacao.apta = None if avaliacao.nota_geral is None else avaliacao.nota_geral >= settings.NOTA_CORTE_APTIDAO
    avaliacao.save(update_fields=['nota_geral', 'nivel_maturidade', 'apta'])
    return avaliacao


def _nota_normalizada(itens):
    peso_total = sum(peso for peso, _ in itens)
    alcancado = sum(peso * (valor - ESCALA_MIN) / (ESCALA_MAX - ESCALA_MIN) for peso, valor in itens)
    return alcancado / peso_total * 100


def _nivel(nota_geral):
    """Cinco níveis de maturidade, um a cada 20 pontos."""
    return None if nota_geral is None else min(5, int(nota_geral // 20) + 1)


def _objetivas_ativas(avaliacao):
    return Pergunta.objects.filter(
        dimensao__questionario=avaliacao.questionario, tipo=TipoPergunta.OBJETIVA, ativa=True,
    )


def _objetivas_sem_resposta(avaliacao):
    respondidas = avaliacao.respostas.filter(valor_objetivo__isnull=False).values('pergunta_id')
    return list(_objetivas_ativas(avaliacao).exclude(id__in=respondidas))


def _exigir_rascunho(avaliacao):
    if avaliacao.status != StatusAvaliacao.RASCUNHO:
        raise AvaliacaoJaSubmetida()
