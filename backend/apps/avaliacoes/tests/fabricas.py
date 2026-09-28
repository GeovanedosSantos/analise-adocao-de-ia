from apps.avaliacoes.models import Avaliacao, Resposta
from apps.questionarios.models import TipoPergunta
from apps.questionarios.tests.fabricas import perguntas


def criar_avaliacao(empresa, questionario, **campos):
    return Avaliacao.objects.create(empresa=empresa, questionario=questionario, **campos)


def responder_objetivas(avaliacao, valores):
    """`valores` segue a ordem das perguntas objetivas do questionário (dimensão, ordem)."""
    for pergunta, valor in zip(perguntas(avaliacao.questionario, TipoPergunta.OBJETIVA), valores, strict=True):
        Resposta.objects.update_or_create(avaliacao=avaliacao, pergunta=pergunta, defaults={'valor_objetivo': valor})


def responder_dissertativas(avaliacao, texto='Temos um data lake com dados de vendas.'):
    for pergunta in perguntas(avaliacao.questionario, TipoPergunta.DISSERTATIVA):
        Resposta.objects.update_or_create(avaliacao=avaliacao, pergunta=pergunta, defaults={'texto_aberto': texto})
