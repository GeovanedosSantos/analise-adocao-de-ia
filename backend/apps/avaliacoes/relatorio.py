"""Relatório da avaliação em PDF, gerado com WeasyPrint.

O HTML é montado na thread da requisição, que tem o tenant do RLS definido. Só a conversão para PDF,
que não toca o banco, roda numa thread à parte para poder ser limitada a PDF_TIMEOUT segundos.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as TempoEsgotado

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from rest_framework.exceptions import APIException

from . import graficos
from .models import Avaliacao, StatusAvaliacao

logger = logging.getLogger(__name__)

# Poucas threads: uma conversão que estoura o tempo continua rodando até o fim e ocupa a vaga
_conversor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='pdf')


class PdfIndisponivel(APIException):
    status_code = 503
    default_detail = 'Não foi possível gerar o PDF agora. Tente novamente.'
    default_code = 'pdf_indisponivel'


def gerar_pdf(avaliacao):
    """Retorna os bytes do PDF. Falha na conversão é tentada de novo; estouro de tempo, não."""
    html = render_to_string('avaliacoes/relatorio.html', _contexto(avaliacao))
    for tentativa in range(1, settings.PDF_TENTATIVAS + 1):
        futuro = _conversor.submit(_converter, html)
        try:
            return futuro.result(timeout=settings.PDF_TIMEOUT)
        except TempoEsgotado:
            futuro.cancel()
            logger.warning('PDF da avaliação %s passou de %ss', avaliacao.id, settings.PDF_TIMEOUT)
            raise PdfIndisponivel(
                f'A geração do PDF passou de {settings.PDF_TIMEOUT:g} segundos. Tente novamente.', code='pdf_timeout',
            )
        except Exception:
            logger.exception('Falha ao gerar o PDF da avaliação %s (tentativa %s)', avaliacao.id, tentativa)
    raise PdfIndisponivel()


def _converter(html):
    # Importado aqui: o WeasyPrint depende do Pango instalado no sistema, e o resto da API não
    from weasyprint import HTML

    return HTML(string=html).write_pdf()


def _contexto(avaliacao):
    perguntas = {r.pergunta_id: r.pergunta.texto for r in avaliacao.respostas.select_related('pergunta')}
    pontuacoes = list(avaliacao.pontuacoes.all())
    return {
        'avaliacao': avaliacao,
        'empresa': avaliacao.empresa,
        'pontuacoes': pontuacoes,
        'grupos': _plano_por_dimensao(avaliacao, pontuacoes),
        'radar': mark_safe(graficos.radar(
            [p.dimensao.nome for p in pontuacoes],
            [p.nota for p in pontuacoes],
            [getattr(p, 'nota_anterior', None) for p in pontuacoes],
        )),
        'linha_do_tempo': mark_safe(graficos.linha_do_tempo(_historico(avaliacao))),
        'analises': [
            {'pergunta': perguntas[r.pergunta_id], **r.feedback_ia}
            for r in avaliacao.respostas.all() if r.feedback_ia
        ],
        'gerado_em': timezone.localtime(),
    }


def _plano_por_dimensao(avaliacao, pontuacoes):
    """Plano de ação agrupado por dimensão (US06); os grupos seguem a melhor posição de cada um."""
    por_codigo = {p.dimensao.codigo: p for p in pontuacoes}
    grupos = {}
    for item in avaliacao.recomendacoes.select_related('recomendacao'):
        codigo = item.recomendacao.dimensao_codigo
        pontuacao = por_codigo.get(codigo)
        grupo = grupos.setdefault(codigo, {
            'nome': pontuacao.dimensao.nome if pontuacao else codigo,
            'nota': item.nota_dimensao,
            'prioritaria': bool(pontuacao and pontuacao.prioritaria),
            'itens': [],
        })
        grupo['itens'].append(item)
    return list(grupos.values())


def _historico(avaliacao):
    """Índice geral das avaliações concluídas da empresa até esta, para a linha do tempo."""
    anteriores = Avaliacao.objects.filter(
        empresa_id=avaliacao.empresa_id, status=StatusAvaliacao.CONCLUIDA, data_fim__lt=avaliacao.data_fim,
        nota_geral__isnull=False,
    ).exclude(pk=avaliacao.pk).order_by('data_fim').values_list('data_fim', 'nota_geral')
    pontos = [*anteriores, (avaliacao.data_fim, avaliacao.nota_geral)]
    return [(timezone.localtime(data).strftime('%d/%m/%y'), nota) for data, nota in pontos if nota is not None]
