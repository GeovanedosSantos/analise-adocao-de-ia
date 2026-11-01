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
        pendentes = _pendentes(avaliacao_id, empresa_id)
        contextos = _contextos_por_dimensao(avaliacao_id, empresa_id) if pendentes else {}
        for resposta in pendentes:
            contexto = contextos.get(resposta.pergunta.dimensao_id)
            analise = llm.analisar_resposta(resposta.pergunta.texto, resposta.texto_aberto, contexto)
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


# Quantas afirmações objetivas de cada ponta vão para o prompt: discordância (1-2) e concordância (4-5)
ITENS_POR_PONTA = 2


def _contextos_por_dimensao(avaliacao_id, empresa_id):
    """O que o sistema já sabe da empresa em cada dimensão, para a IA analisar com contexto.

    {dimensao_id: {setor, dimensao, descricao_dimensao, fatores, nota, menor_concordancia, maior_concordancia}}
    """
    with transacao_da_empresa(empresa_id):
        avaliacao = Avaliacao.objects.select_related('empresa').get(pk=avaliacao_id)
        notas = {p.dimensao_id: p.nota for p in avaliacao.pontuacoes.all()}
        objetivas = {}
        for r in (
            avaliacao.respostas.filter(valor_objetivo__isnull=False)
            .select_related('pergunta')
            .order_by('valor_objetivo', 'pergunta__ordem')
        ):
            objetivas.setdefault(r.pergunta.dimensao_id, []).append((r.pergunta.texto, r.valor_objetivo))
        dimensoes = avaliacao.questionario.dimensoes.prefetch_related('fatores')
        contextos = {}
        for dimensao in dimensoes:
            # Já vêm do menor para o maior valor; o 3 (neutro) não entra em nenhuma ponta
            itens = objetivas.get(dimensao.id, [])
            menores = [i for i in itens if i[1] <= 2][:ITENS_POR_PONTA]
            maiores = [i for i in reversed(itens) if i[1] >= 4][:ITENS_POR_PONTA]
            contextos[dimensao.id] = {
                'setor': avaliacao.empresa.setor,
                'dimensao': dimensao.nome,
                'descricao_dimensao': dimensao.descricao,
                'fatores': [f.nome for f in dimensao.fatores.all()],
                'nota': notas.get(dimensao.id),
                'menor_concordancia': menores,
                'maior_concordancia': maiores,
            }
    return contextos


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
