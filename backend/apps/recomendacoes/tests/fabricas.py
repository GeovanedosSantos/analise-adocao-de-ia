from apps.recomendacoes.models import Nivel, Prazo, Recomendacao


def criar_recomendacao(codigo, dimensao='dados', faixa=(0, 100), **campos):
    minima, maxima = faixa
    padrao = {
        'titulo': f'Ação {codigo}', 'descricao': 'Faça algo.', 'prazo': Prazo.CURTO,
        'prioridade': Nivel.MEDIO, 'esforco': Nivel.MEDIO, 'impacto': Nivel.MEDIO,
    }
    return Recomendacao.objects.create(
        codigo=codigo, dimensao_codigo=dimensao, nota_minima=minima, nota_maxima=maxima, **{**padrao, **campos},
    )
