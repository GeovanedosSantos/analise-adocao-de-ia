from django.test import TestCase, override_settings

from apps.avaliacoes.services import calcular_pontuacao
from apps.contas.tests.fabricas import criar_empresa
from apps.questionarios.models import Dimensao, Pergunta, TipoPergunta
from apps.questionarios.tests.fabricas import criar_questionario

from .fabricas import criar_avaliacao, responder_objetivas


@override_settings(NOTA_CORTE_APTIDAO=70)
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
        self.assertEqual((self.avaliacao.nota_geral, self.avaliacao.nivel_maturidade), (100.0, 5))

        responder_objetivas(self.avaliacao, [1, 1, 1])
        calcular_pontuacao(self.avaliacao)
        self.assertEqual((self.avaliacao.nota_geral, self.avaliacao.nivel_maturidade), (0.0, 1))

    def test_nivel_de_maturidade_e_aptidao(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])  # nota geral 50

        calcular_pontuacao(self.avaliacao)

        self.assertEqual(self.avaliacao.nivel_maturidade, 3)
        self.assertFalse(self.avaliacao.apta)

    def test_empresa_e_apta_quando_atinge_a_nota_de_corte(self):
        responder_objetivas(self.avaliacao, [5, 4, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertGreaterEqual(self.avaliacao.nota_geral, 70)
        self.assertTrue(self.avaliacao.apta)

    def test_menor_dimensao_e_a_prioritaria_e_recalculo_nao_deixa_duas(self):
        responder_objetivas(self.avaliacao, [5, 1, 5])
        calcular_pontuacao(self.avaliacao)
        responder_objetivas(self.avaliacao, [5, 5, 1])

        calcular_pontuacao(self.avaliacao)

        prioritarias = list(self.avaliacao.pontuacoes.filter(prioritaria=True).values_list('dimensao__nome', flat=True))
        self.assertEqual(prioritarias, ['Pessoas'])

    def test_dimensao_sem_perguntas_objetivas_ativas_nao_entra_no_calculo(self):
        so_texto = Dimensao.objects.create(questionario=self.avaliacao.questionario, nome='Cultura', peso=5, ordem=3)
        Pergunta.objects.create(dimensao=so_texto, texto='Conte.', tipo=TipoPergunta.DISSERTATIVA, peso=1, ordem=1)
        responder_objetivas(self.avaliacao, [5, 1, 5])

        calcular_pontuacao(self.avaliacao)

        self.assertNotIn('Cultura', self.notas())
        self.assertAlmostEqual(self.avaliacao.nota_geral, 50.0)
