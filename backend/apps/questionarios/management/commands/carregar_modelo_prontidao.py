from django.core.management.base import BaseCommand
from django.db import transaction

from apps.questionarios.modelo_prontidao import DIMENSOES, VERSAO
from apps.questionarios.models import Dimensao, Fator, Pergunta, Questionario, TipoPergunta
from apps.recomendacoes.catalogo_inicial import CATALOGO
from apps.recomendacoes.models import Recomendacao


class Command(BaseCommand):
    help = (
        'Carrega o modelo de prontidão (5 dimensões, 19 fatores, 38 itens) e o catálogo inicial. '
        'Publica a versão se nenhuma estiver ativa. Pode rodar mais de uma vez.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        questionario, criado = Questionario.objects.get_or_create(
            versao=VERSAO, defaults={'descricao': 'Modelo de prontidão organizacional para IA (provisório).'},
        )
        if criado:
            self._criar_estrutura(questionario)
        if not Questionario.objects.filter(ativo=True).exists():
            questionario.publicar()
        novas = 0
        for codigo, dimensao, (minima, maxima), titulo, descricao, prazo, prioridade, esforco, impacto, kpi in CATALOGO:
            _, criada = Recomendacao.objects.get_or_create(codigo=codigo, defaults={
                'dimensao_codigo': dimensao, 'nota_minima': minima, 'nota_maxima': maxima, 'titulo': titulo,
                'descricao': descricao, 'prazo': prazo, 'prioridade': prioridade, 'esforco': esforco,
                'impacto': impacto, 'kpi': kpi,
            })
            novas += criada
        self.stdout.write(f'Questionário v{VERSAO} {"criado" if criado else "já existia"}; {novas} recomendações novas.')

    def _criar_estrutura(self, questionario):
        for ordem, (codigo, nome, descricao, peso, aberta, fatores) in enumerate(DIMENSOES, start=1):
            dimensao = Dimensao.objects.create(
                questionario=questionario, codigo=codigo, nome=nome, descricao=descricao, peso=peso, ordem=ordem,
            )
            ordem_pergunta = 0
            for ordem_fator, (nome_fator, definicao, itens) in enumerate(fatores, start=1):
                fator = Fator.objects.create(dimensao=dimensao, nome=nome_fator, descricao=definicao, ordem=ordem_fator)
                for texto in itens:
                    ordem_pergunta += 1
                    Pergunta.objects.create(
                        dimensao=dimensao, fator=fator, texto=texto, tipo=TipoPergunta.OBJETIVA, peso=1,
                        ordem=ordem_pergunta,
                    )
            Pergunta.objects.create(
                dimensao=dimensao, texto=aberta, tipo=TipoPergunta.DISSERTATIVA, peso=1, ordem=ordem_pergunta + 1,
            )
