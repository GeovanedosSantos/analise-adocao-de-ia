from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.avaliacoes.services import calcular_pontuacao, selecionar_recomendacoes
from apps.avaliacoes.tests.fabricas import criar_avaliacao, responder_objetivas
from apps.contas.tests.fabricas import criar_empresa, criar_usuario
from apps.questionarios.tests.fabricas import criar_questionario
from apps.recomendacoes.models import Nivel

from .fabricas import criar_recomendacao


class FaixaTests(TestCase):
    def test_faixa_fecha_embaixo_e_abre_em_cima(self):
        recomendacao = criar_recomendacao('r', faixa=(40, 70))

        self.assertEqual(
            [recomendacao.aplica_a(nota) for nota in (39.9, 40, 69.9, 70)], [False, True, True, False],
        )

    def test_maxima_100_inclui_a_nota_100(self):
        self.assertTrue(criar_recomendacao('r', faixa=(70, 100)).aplica_a(100))

    def test_banco_recusa_faixa_invertida(self):
        with self.assertRaises(IntegrityError):
            criar_recomendacao('r', faixa=(70, 40))


@override_settings(TOTAL_RECOMENDACOES=10)
class SelecaoTests(TestCase):
    """[5, 1, 5] → Dados 25, Pessoas 100. [1, 5, 1] → Dados 75, Pessoas 0."""

    def setUp(self):
        self.avaliacao = criar_avaliacao(criar_empresa(), criar_questionario())

    def plano(self, valores):
        responder_objetivas(self.avaliacao, valores)
        calcular_pontuacao(self.avaliacao)
        selecionar_recomendacoes(self.avaliacao)
        return list(self.avaliacao.recomendacoes.values_list('recomendacao__codigo', flat=True))

    def test_escolhe_pela_faixa_da_nota_de_cada_dimensao(self):
        criar_recomendacao('dados-baixa', 'dados', (0, 40))
        criar_recomendacao('dados-alta', 'dados', (70, 100))
        criar_recomendacao('pessoas-alta', 'pessoas', (70, 100))
        criar_recomendacao('pessoas-baixa', 'pessoas', (0, 40))

        self.assertEqual(self.plano([5, 1, 5]), ['dados-baixa', 'pessoas-alta'])

    def test_ignora_inativas_e_dimensoes_fora_da_avaliacao(self):
        criar_recomendacao('inativa', 'dados', ativa=False)
        criar_recomendacao('outra-dimensao', 'estrategia')
        criar_recomendacao('valida', 'dados')

        self.assertEqual(self.plano([5, 1, 5]), ['valida'])

    def test_ordena_pela_menor_nota_e_depois_por_prioridade_impacto_e_esforco(self):
        criar_recomendacao('pessoas', 'pessoas', prioridade=Nivel.ALTO)
        criar_recomendacao('dados-media', 'dados', prioridade=Nivel.MEDIO)
        criar_recomendacao('dados-alta-esforco-alto', 'dados', prioridade=Nivel.ALTO, esforco=Nivel.ALTO)
        criar_recomendacao('dados-alta-esforco-baixo', 'dados', prioridade=Nivel.ALTO, esforco=Nivel.BAIXO)
        criar_recomendacao('dados-alta-impacto-alto', 'dados', prioridade=Nivel.ALTO, impacto=Nivel.ALTO)

        self.assertEqual(self.plano([5, 1, 5]), [
            'dados-alta-impacto-alto', 'dados-alta-esforco-baixo', 'dados-alta-esforco-alto', 'dados-media', 'pessoas',
        ])

    def test_salva_no_maximo_dez_com_posicao_e_nota_da_dimensao(self):
        for i in range(12):
            criar_recomendacao(f'r{i:02}', 'dados')

        plano = self.plano([5, 1, 5])

        self.assertEqual(plano, [f'r{i:02}' for i in range(10)])
        primeira = self.avaliacao.recomendacoes.first()
        self.assertEqual((primeira.posicao, primeira.nota_dimensao), (1, 25.0))

    def test_recalcular_substitui_o_plano(self):
        criar_recomendacao('dados-baixa', 'dados', (0, 40))
        criar_recomendacao('dados-alta', 'dados', (70, 100))
        self.plano([5, 1, 5])

        self.assertEqual(self.plano([1, 5, 1]), ['dados-alta'])


class CatalogoApiTests(APITestCase):
    def test_lista_ativas_da_versao_publicada_na_ordem_das_dimensoes(self):
        criar_questionario()  # Dados, depois Pessoas
        criar_recomendacao('pessoas-1', 'pessoas')
        criar_recomendacao('dados-alta', 'dados', (70, 100))
        criar_recomendacao('dados-baixa', 'dados', (0, 40))
        criar_recomendacao('fora-da-versao', 'cultura')
        criar_recomendacao('inativa', 'dados', ativa=False)
        self.client.force_authenticate(criar_usuario(criar_empresa()))

        resposta = self.client.get('/api/v1/recomendacoes/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [(r['codigo'], r['dimensao_nome']) for r in resposta.data],
            [('dados-baixa', 'Dados'), ('dados-alta', 'Dados'), ('pessoas-1', 'Pessoas')],
        )

    def test_exige_login(self):
        self.assertEqual(self.client.get('/api/v1/recomendacoes/').status_code, 401)


class CadastroTests(TestCase):
    def test_exige_dimensao_cadastrada(self):
        criar_questionario()
        valida = criar_recomendacao('ok', 'dados')
        invalida = criar_recomendacao('nao', 'inexistente')

        valida.full_clean()
        with self.assertRaises(ValidationError) as erro:
            invalida.full_clean()
        self.assertIn('dimensao_codigo', erro.exception.message_dict)
