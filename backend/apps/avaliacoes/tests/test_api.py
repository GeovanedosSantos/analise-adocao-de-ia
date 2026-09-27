from unittest import mock

from rest_framework.test import APITestCase

from apps.avaliacoes.models import Avaliacao, StatusAvaliacao
from apps.contas.models import AuditoriaAcesso
from apps.contas.tests.fabricas import criar_empresa, criar_usuario
from apps.questionarios.models import Questionario, TipoPergunta
from apps.questionarios.tests.fabricas import criar_questionario, perguntas

from .fabricas import criar_avaliacao, responder_dissertativas, responder_objetivas

URL = '/api/v1/avaliacoes/'


class ApiTestCase(APITestCase):
    def setUp(self):
        self.questionario = criar_questionario()
        self.empresa = criar_empresa('Empresa A')
        self.client.force_authenticate(criar_usuario(self.empresa))
        self.objetivas = perguntas(self.questionario, TipoPergunta.OBJETIVA)
        self.dissertativa = perguntas(self.questionario, TipoPergunta.DISSERTATIVA)[0]


class CriarAvaliacaoTests(ApiTestCase):
    def test_cria_rascunho_na_versao_ativa(self):
        resposta = self.client.post(URL)

        self.assertEqual(resposta.status_code, 201)
        avaliacao = Avaliacao.objects.get(id=resposta.data['id'])
        self.assertEqual((avaliacao.empresa, avaliacao.questionario), (self.empresa, self.questionario))
        self.assertEqual(avaliacao.status, StatusAvaliacao.RASCUNHO)

    def test_retoma_o_rascunho_existente_em_vez_de_criar_outro(self):
        primeira = self.client.post(URL)

        segunda = self.client.post(URL)

        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(segunda.data['id'], primeira.data['id'])
        self.assertEqual(Avaliacao.objects.count(), 1)

    def test_duas_requisicoes_simultaneas_nao_quebram(self):
        """Outra requisição cria o rascunho entre a verificação e a criação (ex.: StrictMode do React)."""
        buscar_ativo = Questionario.objects.get

        def concorrente_cria_antes(*args, **kwargs):
            questionario = buscar_ativo(*args, **kwargs)
            Avaliacao.objects.create(empresa=self.empresa, questionario=questionario)
            return questionario

        with mock.patch('apps.avaliacoes.services.Questionario.objects.get', side_effect=concorrente_cria_antes):
            resposta = self.client.post(URL)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Avaliacao.objects.count(), 1)


class IsolamentoEntreEmpresasTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.outra_empresa = criar_empresa('Empresa B')
        self.avaliacao_alheia = criar_avaliacao(self.outra_empresa, self.questionario)

    def test_listagem_so_mostra_avaliacoes_da_propria_empresa(self):
        propria = criar_avaliacao(self.empresa, self.questionario)

        resposta = self.client.get(URL)

        self.assertEqual([a['id'] for a in resposta.data], [str(propria.id)])

    def test_acesso_a_avaliacao_de_outra_empresa_retorna_403_e_audita(self):
        resposta = self.client.get(f'{URL}{self.avaliacao_alheia.id}/')

        self.assertEqual(resposta.status_code, 403)
        registro = AuditoriaAcesso.objects.get()
        self.assertEqual(registro.empresa_usuario_id, self.empresa.id)
        self.assertEqual(registro.empresa_recurso_id, self.outra_empresa.id)
        self.assertEqual(registro.recurso_id, str(self.avaliacao_alheia.id))

    def test_escrita_em_avaliacao_de_outra_empresa_e_bloqueada(self):
        resposta = self.client.patch(
            f'{URL}{self.avaliacao_alheia.id}/rascunho/',
            {'respostas': [{'pergunta': str(self.objetivas[0].id), 'valor_objetivo': 5}]},
            format='json',
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(self.avaliacao_alheia.respostas.exists())

    def test_avaliacao_inexistente_retorna_404(self):
        resposta = self.client.get(f'{URL}00000000-0000-0000-0000-000000000000/')

        self.assertEqual(resposta.status_code, 404)


class RascunhoTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.avaliacao = criar_avaliacao(self.empresa, self.questionario)
        self.url = f'{URL}{self.avaliacao.id}/rascunho/'

    def salvar(self, *respostas):
        return self.client.patch(self.url, {'respostas': list(respostas)}, format='json')

    def test_salva_e_recupera_o_rascunho(self):
        self.salvar({'pergunta': str(self.objetivas[0].id), 'valor_objetivo': 4})
        self.salvar(
            {'pergunta': str(self.objetivas[0].id), 'valor_objetivo': 2},
            {'pergunta': str(self.dissertativa.id), 'texto_aberto': 'Ainda planejando.'},
        )

        detalhe = self.client.get(f'{URL}{self.avaliacao.id}/')

        respostas = {r['pergunta']: r for r in detalhe.data['respostas']}
        self.assertEqual(len(respostas), 2)
        self.assertEqual(respostas[str(self.objetivas[0].id)]['valor_objetivo'], 2)
        self.assertEqual(respostas[str(self.dissertativa.id)]['texto_aberto'], 'Ainda planejando.')

    def test_recusa_pergunta_de_outra_versao(self):
        outra_versao = criar_questionario('9.9', publicar=False)

        resposta = self.salvar({'pergunta': str(perguntas(outra_versao)[0].id), 'valor_objetivo': 3})

        self.assertEqual(resposta.status_code, 400)

    def test_recusa_valor_fora_da_escala(self):
        resposta = self.salvar({'pergunta': str(self.objetivas[0].id), 'valor_objetivo': 6})

        self.assertEqual(resposta.status_code, 400)

    def test_recusa_tipo_de_resposta_incompativel_com_a_pergunta(self):
        valor_em_dissertativa = self.salvar({'pergunta': str(self.dissertativa.id), 'valor_objetivo': 3})
        texto_em_objetiva = self.salvar({'pergunta': str(self.objetivas[0].id), 'texto_aberto': 'x'})

        self.assertEqual((valor_em_dissertativa.status_code, texto_em_objetiva.status_code), (400, 400))

    def test_nao_altera_avaliacao_ja_submetida(self):
        self.avaliacao.status = StatusAvaliacao.CONCLUIDA
        self.avaliacao.save()

        resposta = self.salvar({'pergunta': str(self.objetivas[0].id), 'valor_objetivo': 3})

        self.assertEqual(resposta.status_code, 409)


@mock.patch('apps.avaliacoes.services.processar_respostas_abertas.delay')
class SubmeterTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.avaliacao = criar_avaliacao(self.empresa, self.questionario)
        self.url = f'{URL}{self.avaliacao.id}/submeter/'

    def test_exige_todas_as_objetivas_respondidas(self, delay):
        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 400)
        self.avaliacao.refresh_from_db()
        self.assertEqual(self.avaliacao.status, StatusAvaliacao.RASCUNHO)

    def test_com_respostas_abertas_retorna_202_e_enfileira_a_ia(self, delay):
        responder_objetivas(self.avaliacao, [5, 1, 5])
        responder_dissertativas(self.avaliacao)

        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 202)
        self.assertEqual(resposta.data['status'], StatusAvaliacao.PROCESSANDO_IA)
        self.assertAlmostEqual(resposta.data['nota_geral'], 50.0)
        delay.assert_called_once_with(str(self.avaliacao.id))

    def test_sem_respostas_abertas_conclui_sem_chamar_a_ia(self, delay):
        responder_objetivas(self.avaliacao, [5, 1, 5])

        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['status'], StatusAvaliacao.CONCLUIDA)
        delay.assert_not_called()

    def test_nao_submete_duas_vezes(self, delay):
        responder_objetivas(self.avaliacao, [5, 1, 5])
        self.client.post(self.url)

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 409)

    def test_consulta_de_status_para_polling(self, delay):
        responder_objetivas(self.avaliacao, [5, 1, 5])
        responder_dissertativas(self.avaliacao)
        self.client.post(self.url)

        resposta = self.client.get(f'{URL}{self.avaliacao.id}/status/')

        self.assertEqual(resposta.data, {'id': str(self.avaliacao.id), 'status': StatusAvaliacao.PROCESSANDO_IA})
