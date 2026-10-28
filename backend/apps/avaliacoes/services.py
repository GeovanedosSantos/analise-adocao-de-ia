from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import prefetch_related_objects
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.questionarios.models import Pergunta, Questionario, TipoPergunta
from apps.recomendacoes.models import Nivel, Recomendacao

from .models import (
    ESCALA_MAX, ESCALA_MIN, Avaliacao, PontuacaoDimensao, RecomendacaoAvaliacao, Resposta, StatusAvaliacao,
)
from .tasks import processar_ia


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


def descartar_rascunho(avaliacao):
    """Recomeça o questionário (UC02 FA02): apaga as respostas parciais e mantém o rascunho."""
    _exigir_rascunho(avaliacao)
    avaliacao.respostas.all().delete()


def submeter(avaliacao):
    """Fecha a avaliação, calcula a nota, monta o plano de ação e, se houver trabalho para a IA, enfileira.

    A IA analisa as respostas abertas e ordena o plano de ação; com uma recomendação só, não há o que ordenar.
    """
    _exigir_rascunho(avaliacao)
    faltantes = _objetivas_sem_resposta(avaliacao)
    if faltantes:
        raise ValidationError({'perguntas_sem_resposta': [str(p.id) for p in faltantes]})

    calcular_pontuacao(avaliacao)
    selecionar_recomendacoes(avaliacao)
    tem_abertas = avaliacao.respostas.exclude(texto_aberto='').exists()
    precisa_ia = tem_abertas or avaliacao.recomendacoes.count() > 1
    avaliacao.status = StatusAvaliacao.PROCESSANDO_IA if precisa_ia else StatusAvaliacao.CONCLUIDA
    avaliacao.data_fim = timezone.now()
    avaliacao.save(update_fields=['status', 'data_fim'])
    if precisa_ia:
        transaction.on_commit(lambda: processar_ia.delay(str(avaliacao.id), str(avaliacao.empresa_id)))
    return avaliacao


@transaction.atomic
def calcular_pontuacao(avaliacao):
    """Motor determinístico (RF05, RF06, RF07).

    - Nota da dimensão: média das objetivas ponderada pelo peso da pergunta, levada de 0 a 100.
    - Nota geral: média das dimensões ponderada pelo peso da dimensão.
    - Dimensão prioritária: a de menor nota. Empate na nota: a de maior peso. Empate também no
      peso: todas as empatadas (US04).
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
        menor_nota = min(p.nota for p in pontuacoes)
        maior_peso = max(p.dimensao.peso for p in pontuacoes if p.nota == menor_nota)
        for pontuacao in pontuacoes:
            pontuacao.prioritaria = pontuacao.nota == menor_nota and pontuacao.dimensao.peso == maior_peso
    avaliacao.pontuacoes.all().delete()
    PontuacaoDimensao.objects.bulk_create(pontuacoes)

    peso_total = sum(p.dimensao.peso for p in pontuacoes)
    avaliacao.nota_geral = sum(p.nota * p.dimensao.peso for p in pontuacoes) / peso_total if peso_total else None
    avaliacao.nivel_prontidao = _nivel(avaliacao.nota_geral)
    avaliacao.save(update_fields=['nota_geral', 'nivel_prontidao'])
    return avaliacao


# Desempate do plano de ação: prioridade e impacto altos primeiro, esforço baixo primeiro
_RELEVANCIA = {Nivel.ALTO: 0, Nivel.MEDIO: 1, Nivel.BAIXO: 2}


def recomendacoes_aplicaveis(avaliacao):
    """Recomendações ativas cuja dimensão (pelo código) teve nota dentro da faixa delas, como [(nota, recomendação)].

    Ordem pelas faixas: dimensões de menor nota primeiro; depois prioridade, impacto e esforço.
    """
    notas = {p.dimensao.codigo: p.nota for p in avaliacao.pontuacoes.select_related('dimensao')}
    candidatas = [
        (notas[r.dimensao_codigo], r)
        for r in Recomendacao.objects.filter(ativa=True, dimensao_codigo__in=notas)
        if r.aplica_a(notas[r.dimensao_codigo])
    ]
    candidatas.sort(key=lambda par: (
        par[0], _RELEVANCIA[par[1].prioridade], _RELEVANCIA[par[1].impacto], -_RELEVANCIA[par[1].esforco],
        par[1].codigo,
    ))
    return candidatas


@transaction.atomic
def selecionar_recomendacoes(avaliacao, ranking=None):
    """Grava o plano de ação (RF10, UC12): as TOTAL_RECOMENDACOES primeiras recomendações aplicáveis.

    Sem `ranking`, vale a ordem pelas faixas, que já fica disponível enquanto a IA trabalha (US05).
    `ranking` é a lista de códigos na ordem da IA (tasks.processar_ia); o que não estiver nela vai para o fim.
    """
    candidatas = recomendacoes_aplicaveis(avaliacao)
    if ranking is not None:
        posicao_ia = {codigo: i for i, codigo in enumerate(ranking)}
        candidatas.sort(key=lambda par: posicao_ia.get(par[1].codigo, len(ranking)))
    avaliacao.recomendacoes.all().delete()
    RecomendacaoAvaliacao.objects.bulk_create(
        RecomendacaoAvaliacao(avaliacao=avaliacao, recomendacao=r, posicao=posicao, nota_dimensao=nota)
        for posicao, (nota, r) in enumerate(candidatas[:settings.TOTAL_RECOMENDACOES], start=1)
    )


def anexar_deltas(avaliacao):
    """Deriva os deltas (RF12) na leitura: variação percentual em relação à última avaliação concluída antes desta."""
    referencia = avaliacao.data_fim or timezone.now()
    anterior = (
        Avaliacao.objects.filter(
            empresa_id=avaliacao.empresa_id, status=StatusAvaliacao.CONCLUIDA, data_fim__lt=referencia,
        )
        .exclude(pk=avaliacao.pk)
        .order_by('-data_fim')
        .first()
    )
    notas_anteriores = dict(anterior.pontuacoes.values_list('dimensao__codigo', 'nota')) if anterior else {}
    # Os deltas ficam nas instâncias em cache, que são as mesmas que o serializer lê depois
    prefetch_related_objects([avaliacao], 'pontuacoes__dimensao__fatores')
    _aplicar_deltas(avaliacao, anterior, notas_anteriores)
    return avaliacao


def anexar_deltas_em_lote(avaliacoes, com_dimensoes=False):
    """Como `anexar_deltas`, para avaliações de uma mesma empresa já carregadas (listagem e histórico).

    As anteriores são procuradas entre as próprias `avaliacoes`, que precisam incluir todas as concluídas
    da empresa. Com `com_dimensoes`, as pontuações devem vir pré-carregadas com a dimensão.
    """
    concluidas = sorted(
        (a for a in avaliacoes if a.status == StatusAvaliacao.CONCLUIDA and a.data_fim), key=lambda a: a.data_fim,
    )
    for avaliacao in avaliacoes:
        referencia = avaliacao.data_fim or timezone.now()
        anterior = next((c for c in reversed(concluidas) if c.data_fim < referencia and c.pk != avaliacao.pk), None)
        notas_anteriores = None
        if com_dimensoes:
            notas_anteriores = {p.dimensao.codigo: p.nota for p in anterior.pontuacoes.all()} if anterior else {}
        _aplicar_deltas(avaliacao, anterior, notas_anteriores)
    return avaliacoes


def _aplicar_deltas(avaliacao, anterior, notas_anteriores):
    """Pareia as dimensões pelo código, que se mantém entre versões do questionário.

    `notas_anteriores` None: calcula só o delta da nota geral (a listagem não traz pontuações).
    As notas anteriores também ficam expostas, porque o delta não existe quando a anterior é 0.
    """
    avaliacao.nota_geral_anterior = anterior.nota_geral if anterior else None
    avaliacao.delta_nota_geral = _delta(avaliacao.nota_geral, avaliacao.nota_geral_anterior)
    if notas_anteriores is not None:
        for pontuacao in avaliacao.pontuacoes.all():
            pontuacao.nota_anterior = notas_anteriores.get(pontuacao.dimensao.codigo)
            pontuacao.delta_percentual = _delta(pontuacao.nota, pontuacao.nota_anterior)


def _delta(atual, anterior):
    """Variação percentual (RF12): de 50 para 75 é +50%. Sem anterior, ou com anterior 0, não há variação."""
    if atual is None or not anterior:
        return None
    return (atual - anterior) / anterior * 100


def _nota_normalizada(itens):
    peso_total = sum(peso for peso, _ in itens)
    alcancado = sum(peso * (valor - ESCALA_MIN) / (ESCALA_MAX - ESCALA_MIN) for peso, valor in itens)
    return alcancado / peso_total * 100


def _nivel(nota_geral):
    """Cinco níveis de prontidão, um a cada 20 pontos."""
    return None if nota_geral is None else min(5, int(nota_geral // 20) + 1)


def _objetivas_ativas(avaliacao):
    return Pergunta.objects.filter(
        dimensao__questionario=avaliacao.questionario, dimensao__ativa=True, tipo=TipoPergunta.OBJETIVA, ativa=True,
    )


def _objetivas_sem_resposta(avaliacao):
    respondidas = avaliacao.respostas.filter(valor_objetivo__isnull=False).values('pergunta_id')
    return list(_objetivas_ativas(avaliacao).exclude(id__in=respondidas))


def _exigir_rascunho(avaliacao):
    if avaliacao.status != StatusAvaliacao.RASCUNHO:
        raise AvaliacaoJaSubmetida()
