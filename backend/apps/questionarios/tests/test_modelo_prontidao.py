from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.contas.tests.fabricas import criar_empresa, criar_usuario
from apps.questionarios.models import Dimensao, Fator, Pergunta, Questionario, TipoPergunta
from apps.recomendacoes.models import Recomendacao

from .fabricas import criar_questionario


class CarregarModeloTests(TestCase):
    def carregar(self):
        call_command('carregar_modelo_prontidao', stdout=StringIO())

    def test_cria_5_dimensoes_19_fatores_e_38_itens_publicados(self):
        self.carregar()

        questionario = Questionario.objects.get(ativo=True)
        self.assertEqual(
            list(questionario.dimensoes.values_list('codigo', flat=True)),
            ['tecnologia', 'organizacao', 'dados', 'conhecimento', 'estrategia'],
        )
        self.assertEqual(Fator.objects.filter(dimensao__questionario=questionario).count(), 19)
        objetivas = Pergunta.objects.filter(dimensao__questionario=questionario, tipo=TipoPergunta.OBJETIVA)
        self.assertEqual(objetivas.count(), 38)
        self.assertFalse(objetivas.filter(fator__isnull=True).exists())

    def test_catalogo_cobre_toda_a_escala_de_cada_dimensao(self):
        self.carregar()

        for codigo in Dimensao.objects.values_list('codigo', flat=True):
            faixas = Recomendacao.objects.filter(dimensao_codigo=codigo)
            for nota in (0, 39.9, 40, 69.9, 70, 100):
                self.assertTrue(any(r.aplica_a(nota) for r in faixas), f'{codigo} sem recomendação para nota {nota}')

    def test_pode_rodar_mais_de_uma_vez(self):
        self.carregar()
        self.carregar()

        self.assertEqual(Questionario.objects.count(), 1)


class FatorTests(TestCase):
    def setUp(self):
        self.questionario = criar_questionario(publicar=False)
        self.dados, self.pessoas = self.questionario.dimensoes.all()

    def test_pergunta_nao_aceita_fator_de_outra_dimensao(self):
        fator = Fator.objects.create(dimensao=self.pessoas, nome='Capacitação')

        with self.assertRaises(ValidationError):
            Pergunta.objects.create(dimensao=self.dados, fator=fator, texto='?', tipo=TipoPergunta.OBJETIVA, peso=1)

    def test_nova_versao_copia_os_fatores_e_o_vinculo_das_perguntas(self):
        fator = Fator.objects.create(dimensao=self.dados, nome='Qualidade')
        self.dados.perguntas.filter(tipo=TipoPergunta.OBJETIVA).update(fator=fator)

        v2 = self.questionario.nova_versao('2.0')

        copia = Fator.objects.get(dimensao__questionario=v2)
        self.assertNotEqual(copia.pk, fator.pk)
        self.assertEqual(copia.perguntas.count(), 2)


class InativarDimensaoTests(APITestCase):
    def test_dimensao_da_versao_publicada_nao_pode_ser_inativada(self):
        dimensao = criar_questionario().dimensoes.first()
        dimensao.ativa = False

        with self.assertRaises(ValidationError):
            dimensao.save()

    def test_dimensao_inativa_some_do_questionario(self):
        questionario = criar_questionario(publicar=False)
        questionario.dimensoes.filter(nome='Pessoas').update(ativa=False)
        questionario.publicar()
        self.client.force_authenticate(criar_usuario(criar_empresa()))

        resposta = self.client.get('/api/v1/questionarios/ativo/')

        self.assertEqual([d['nome'] for d in resposta.data['dimensoes']], ['Dados'])
