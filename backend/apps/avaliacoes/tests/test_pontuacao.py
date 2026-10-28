from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.avaliacoes.models import StatusAvaliacao
from apps.avaliacoes.services import anexar_deltas, anexar_deltas_em_lote, calcular_pontuacao
from apps.contas.tests.fabricas import criar_empresa
from apps.questionarios.models import Dimensao, Pergunta, TipoPergunta
from apps.questionarios.tests.fabricas import criar_questionario

from .fabricas import criar_avaliacao, responder_objetivas


class MotorDePontuacaoTests(TestCase):
    """Escala das objetivas: 1 a 5. Ordem das objetivas: Dados/peso 1, Dados/peso 3, Pessoas/peso 1."""

    def setUp(self):
        self.avaliacao = criar_avaliacao(criar_empresa(), criar_questionario())

    def notas(self):
        return {p.dimensao.nome: p.nota for p in self.avaliacao.pontuacoes.select_related('dimensao')}

    def test_nota_da_dimensao_e_normalizada_de_0_a_100_pelos_pesos_das_perguntas(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.notas(), {'Dados': 25.0, 'Pessoas': 100.0})

    def test_indice_geral_pondera_as_dimensoes_pelo_peso(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertAlmostEqual(self.avaliacao.nota_geral, (25 * 2 + 100 * 1) / 3)

    def test_notas_nos_extremos_da_escala(self):
        responder_objetivas(self.avaliacao, [5, 5, 5])
        calcular_pontuacao(self.avaliacao)
        self.assertEqual((self.avaliacao.nota_geral, self.avaliacao.nivel_prontidao), (100.0, 5))

        responder_objetivas(self.avaliacao, [1, 1, 1])
        calcular_pontuacao(self.avaliacao)
        self.assertEqual((self.avaliacao.nota_geral, self.avaliacao.nivel_prontidao), (0.0, 1))

    def test_nivel_de_prontidao(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])  # nota geral 50

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.avaliacao.nivel_prontidao, 3)

    def test_menor_dimensao_e_a_prioritaria_e_recalculo_nao_deixa_duas(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])
        calcular_pontuacao(self.avaliacao)
        responder_objetivas(self.avaliacao, [5, 5, 1])

        calcular_pontuacao(self.avaliacao)

        prioritarias = list(self.avaliacao.pontuacoes.filter(prioritaria=True).values_list('dimensao__nome', flat=True))
        self.assertEqual(prioritarias, ['Pessoas'])

    def prioritarias(self):
        return list(self.avaliacao.pontuacoes.filter(prioritaria=True).values_list('dimensao__nome', flat=True))

    def test_empate_na_menor_nota_prioriza_a_dimensao_de_maior_peso(self):
        responder_objetivas(self.avaliacao, [1, 1, 1])  # Dados (peso 2) e Pessoas (peso 1) com nota 0

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.prioritarias(), ['Dados'])

    def test_empate_na_nota_e_no_peso_marca_todas_as_empatadas(self):
        Dimensao.objects.filter(questionario=self.avaliacao.questionario).update(peso=1)
        responder_objetivas(self.avaliacao, [1, 1, 1])

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.prioritarias(), ['Dados', 'Pessoas'])

    def test_dimensao_inativa_fica_fora_do_calculo(self):
        pessoas = Dimensao.objects.get(questionario=self.avaliacao.questionario, nome='Pessoas')
        self.avaliacao.questionario.ativo = False  # inativar só é permitido fora da versão publicada
        self.avaliacao.questionario.save()
        pessoas.ativa = False
        pessoas.save()
        responder_objetivas(self.avaliacao, [5, 1, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.notas(), {'Dados': 25.0})

    def test_dimensao_sem_perguntas_objetivas_ativas_nao_entra_no_calculo(self):
        so_texto = Dimensao.objects.create(questionario=self.avaliacao.questionario, nome='Cultura', peso=5, ordem=3)
        Pergunta.objects.create(dimensao=so_texto, texto='Conte.', tipo=TipoPergunta.DISSERTATIVA, peso=1, ordem=1)
        responder_objetivas(self.avaliacao, [5, 1, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertNotIn('Cultura', self.notas())
        self.assertAlmostEqual(self.avaliacao.nota_geral, 50.0)


class DeltasTests(TestCase):
    """Deltas (RF12) em variação percentual, derivados na leitura. Ordem das objetivas: Dados/peso 1,
    Dados/peso 3, Pessoas/peso 1.

    [5, 1, 5] → Dados 25, Pessoas 100, geral 50. [1, 5, 1] → Dados 75, Pessoas 0, geral 50.
    """

    def setUp(self):
        self.empresa = criar_empresa()
        self.questionario = criar_questionario()

    def submetida(self, valores, dias_atras=0, questionario=None, empresa=None):
        avaliacao = criar_avaliacao(
            empresa or self.empresa, questionario or self.questionario,
            status=StatusAvaliacao.CONCLUIDA, data_fim=timezone.now() - timedelta(days=dias_atras),
        )
        responder_objetivas(avaliacao, valores)
        return calcular_pontuacao(avaliacao)

    def deltas(self, avaliacao):
        anexar_deltas(avaliacao)
        return {p.dimensao.codigo: p.delta_percentual for p in avaliacao.pontuacoes.all()}

    def test_primeira_avaliacao_nao_tem_deltas(self):
        avaliacao = self.submetida([5, 1, 5])

        self.assertEqual(self.deltas(avaliacao), {'dados': None, 'pessoas': None})
        self.assertIsNone(avaliacao.delta_nota_geral)

    def test_delta_acompanha_o_historico_atual(self):
        anterior = self.submetida([5, 1, 5], dias_atras=30)
        atual = self.submetida([1, 5, 1])
        self.assertEqual(self.deltas(atual), {'dados': 200.0, 'pessoas': -100.0})

        anterior.delete()

        self.assertEqual(self.deltas(atual), {'dados': None, 'pessoas': None})

    def test_delta_e_a_variacao_percentual_em_relacao_a_avaliacao_anterior(self):
        self.submetida([5, 1, 5], dias_atras=30)

        atual = self.submetida([1, 5, 1])

        self.assertEqual(self.deltas(atual), {'dados': 200.0, 'pessoas': -100.0})
        self.assertEqual(atual.delta_nota_geral, 0.0)
        self.assertEqual(atual.nota_geral_anterior, 50.0)

    def test_anterior_zero_nao_tem_variacao_mas_expoe_a_nota_anterior(self):
        self.submetida([1, 5, 1], dias_atras=30)  # Pessoas 0

        atual = self.submetida([5, 1, 5])  # Pessoas 100

        self.assertIsNone(self.deltas(atual)['pessoas'])
        self.assertEqual(atual.pontuacoes.all()[1].nota_anterior, 0.0)

    def test_compara_com_a_submissao_mais_recente_da_propria_empresa(self):
        self.submetida([1, 1, 1], dias_atras=60)
        self.submetida([5, 1, 5], dias_atras=30)
        self.submetida([5, 5, 5], dias_atras=1, empresa=criar_empresa('Outra'))
        criar_avaliacao(self.empresa, self.questionario)  # rascunho: não tem data_fim

        atual = self.submetida([1, 5, 1])

        self.assertEqual(self.deltas(atual), {'dados': 200.0, 'pessoas': -100.0})

    def test_delta_ignora_avaliacoes_nao_concluidas_mais_recentes(self):
        self.submetida([5, 1, 5], dias_atras=30)
        for status, dias_atras in (
            (StatusAvaliacao.PROCESSANDO_IA, 2),
            (StatusAvaliacao.ERRO_PROCESSAMENTO, 1),
        ):
            nao_concluida = criar_avaliacao(
                self.empresa,
                self.questionario,
                status=status,
                data_fim=timezone.now() - timedelta(days=dias_atras),
            )
            responder_objetivas(nao_concluida, [1, 5, 1])
            calcular_pontuacao(nao_concluida)

        atual = self.submetida([1, 5, 1])

        self.assertEqual(self.deltas(atual), {'dados': 200.0, 'pessoas': -100.0})

    def test_pareia_dimensoes_pelo_codigo_entre_versoes(self):
        self.submetida([5, 1, 5], dias_atras=30)
        v2 = self.questionario.nova_versao('2.0')
        pessoas = v2.dimensoes.get(codigo='pessoas')
        pessoas.nome = 'Pessoas e Cultura'
        pessoas.save()
        cultura = Dimensao.objects.create(questionario=v2, nome='Cultura', peso=1, ordem=3)
        Pergunta.objects.create(dimensao=cultura, texto='Há abertura a testes?', tipo=TipoPergunta.OBJETIVA, peso=1)
        v2.publicar()

        atual = self.submetida([1, 5, 1, 5], questionario=v2)

        self.assertEqual(self.deltas(atual), {'dados': 200.0, 'pessoas': -100.0, 'cultura': None})

    def test_avaliacao_antiga_nao_compara_com_as_posteriores(self):
        antiga = self.submetida([5, 1, 5], dias_atras=30)
        self.submetida([1, 5, 1])

        self.assertEqual(self.deltas(antiga), {'dados': None, 'pessoas': None})

    def test_em_lote_da_o_mesmo_resultado_que_individualmente(self):
        self.submetida([1, 1, 1], dias_atras=60)
        self.submetida([5, 1, 5], dias_atras=30)
        self.submetida([1, 5, 1])
        criar_avaliacao(self.empresa, self.questionario)  # rascunho, sem notas
        carregar = lambda: list(self.empresa.avaliacoes.prefetch_related('pontuacoes__dimensao'))  # noqa: E731

        lote = anexar_deltas_em_lote(carregar(), com_dimensoes=True)
        individuais = [anexar_deltas(a) for a in carregar()]

        def resumo(avaliacoes):
            return [
                (a.delta_nota_geral, [getattr(p, 'delta_percentual', None) for p in a.pontuacoes.all()])
                for a in avaliacoes
            ]
        self.assertEqual(resumo(lote), resumo(individuais))
        self.assertEqual(resumo(lote)[1], (0.0, [200.0, -100.0]))
