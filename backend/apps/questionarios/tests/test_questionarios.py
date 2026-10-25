from django.db import IntegrityError
from rest_framework.test import APITestCase

from apps.contas.tests.fabricas import criar_empresa, criar_usuario
from apps.questionarios.models import Dimensao, Pergunta, Questionario, TipoPergunta

from .fabricas import criar_questionario, perguntas


class VersionamentoTests(APITestCase):
    def test_publicar_nova_versao_arquiva_a_anterior(self):
        v1 = criar_questionario('1.0')
        v2 = criar_questionario('1.1')

        v1.refresh_from_db()
        self.assertFalse(v1.ativo)
        self.assertTrue(v2.ativo)
        self.assertEqual(Questionario.objects.get(ativo=True), v2)

    def test_versao_e_unica(self):
        criar_questionario('1.0')

        with self.assertRaises(IntegrityError):
            Questionario.objects.create(versao='1.0')

    def test_nova_versao_copia_a_estrutura_sem_publicar(self):
        v1 = criar_questionario('1.0')

        v2 = v1.nova_versao('2.0')

        self.assertFalse(v2.ativo)
        self.assertEqual(
            [(p.dimensao.nome, p.texto, p.tipo, p.peso) for p in perguntas(v2)],
            [(p.dimensao.nome, p.texto, p.tipo, p.peso) for p in perguntas(v1)],
        )
        self.assertFalse(set(p.id for p in perguntas(v1)) & set(p.id for p in perguntas(v2)))

    def test_nova_versao_mantem_o_codigo_mesmo_se_o_nome_mudar_depois(self):
        v1 = criar_questionario('1.0')
        v1.dimensoes.filter(nome='Pessoas').update(codigo='capital-humano')

        v2 = v1.nova_versao('2.0')
        pessoas = v2.dimensoes.get(nome='Pessoas')
        pessoas.nome = 'Pessoas e Cultura'
        pessoas.save()

        self.assertEqual(
            list(v2.dimensoes.values_list('codigo', 'nome')),
            [('dados', 'Dados'), ('capital-humano', 'Pessoas e Cultura')],
        )


class CodigoDimensaoTests(APITestCase):
    def test_codigo_em_branco_e_gerado_a_partir_do_nome(self):
        questionario = criar_questionario('1.0')

        dimensao = Dimensao.objects.create(questionario=questionario, nome='Estratégia de Negócio', peso=1)

        self.assertEqual(dimensao.codigo, 'estrategia-de-negocio')

    def test_codigo_e_unico_na_versao(self):
        questionario = criar_questionario('1.0')

        with self.assertRaises(IntegrityError):
            Dimensao.objects.create(questionario=questionario, codigo='dados', nome='Dados 2', peso=1)

    def test_mesmo_codigo_pode_repetir_em_outra_versao(self):
        criar_questionario('1.0')
        v2 = criar_questionario('2.0')

        self.assertTrue(v2.dimensoes.filter(codigo='dados').exists())


class QuestionarioAtivoApiTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(criar_usuario(criar_empresa()))

    def test_retorna_versao_ativa_agrupada_por_dimensao(self):
        questionario = criar_questionario('1.0')
        inativa = Pergunta.objects.create(
            dimensao=questionario.dimensoes.get(nome='Pessoas'), texto='Obsoleta', tipo=TipoPergunta.OBJETIVA,
            peso=1, ordem=9, ativa=False,
        )

        resposta = self.client.get('/api/v1/questionarios/ativo/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['versao'], '1.0')
        self.assertEqual(
            [(d['codigo'], d['nome']) for d in resposta.data['dimensoes']], [('dados', 'Dados'), ('pessoas', 'Pessoas')],
        )
        ids = [p['id'] for d in resposta.data['dimensoes'] for p in d['perguntas']]
        self.assertEqual(ids, [str(p.id) for p in perguntas(questionario) if p.ativa])
        self.assertNotIn(str(inativa.id), ids)

    def test_rascunho_antigo_carrega_a_propria_versao_mesmo_apos_nova_publicacao(self):
        v1 = criar_questionario('1.0')
        criar_questionario('2.0')

        resposta = self.client.get(f'/api/v1/questionarios/{v1.id}/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['versao'], '1.0')
        self.assertEqual(len(resposta.data['dimensoes']), 2)

    def test_sem_versao_ativa_retorna_404(self):
        criar_questionario('1.0', publicar=False)

        resposta = self.client.get('/api/v1/questionarios/ativo/')

        self.assertEqual(resposta.status_code, 404)
