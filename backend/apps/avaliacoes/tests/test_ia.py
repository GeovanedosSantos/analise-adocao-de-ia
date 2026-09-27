import json
from unittest import mock

import requests
from django.test import TestCase, override_settings

from apps.avaliacoes import llm
from apps.avaliacoes.models import StatusAvaliacao
from apps.avaliacoes.tasks import processar_respostas_abertas
from apps.contas.tests.fabricas import criar_empresa
from apps.questionarios.tests.fabricas import criar_questionario

from .fabricas import criar_avaliacao, responder_dissertativas, responder_objetivas

ANALISE_VALIDA = {'analise_qualitativa': 'Base de dados madura.', 'pontos_fortes': ['data lake'], 'riscos': []}


def resposta_ollama(conteudo):
    resposta = mock.Mock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = {'response': conteudo}
    return resposta


@mock.patch('apps.avaliacoes.llm.requests.post')
class ClienteLlmTests(TestCase):
    def test_retorna_analise_quando_o_json_segue_o_contrato(self, post):
        post.return_value = resposta_ollama(json.dumps(ANALISE_VALIDA))

        self.assertEqual(llm.analisar_resposta('Pergunta?', 'Resposta.'), ANALISE_VALIDA)

    def test_json_fora_do_contrato_e_rejeitado(self, post):
        post.return_value = resposta_ollama(json.dumps({'analise_qualitativa': 'ok'}))

        with self.assertRaises(llm.FalhaInferencia):
            llm.analisar_resposta('Pergunta?', 'Resposta.')

    def test_texto_que_nao_e_json_e_rejeitado(self, post):
        post.return_value = resposta_ollama('Claro! Aqui está a análise...')

        with self.assertRaises(llm.FalhaInferencia):
            llm.analisar_resposta('Pergunta?', 'Resposta.')

    def test_timeout_vira_falha_de_inferencia(self, post):
        post.side_effect = requests.Timeout()

        with self.assertRaises(llm.FalhaInferencia):
            llm.analisar_resposta('Pergunta?', 'Resposta.')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, IA_MAX_TENTATIVAS=3)
@mock.patch('apps.avaliacoes.tasks.llm.analisar_resposta')
class ProcessarRespostasAbertasTests(TestCase):
    def setUp(self):
        self.avaliacao = criar_avaliacao(criar_empresa(), criar_questionario(), status=StatusAvaliacao.PROCESSANDO_IA)
        responder_objetivas(self.avaliacao, [5, 1, 5])
        responder_dissertativas(self.avaliacao)
        self.aberta = self.avaliacao.respostas.get(texto_aberto__gt='')

    def executar(self):
        processar_respostas_abertas.apply(args=[str(self.avaliacao.id)])
        self.avaliacao.refresh_from_db()
        self.aberta.refresh_from_db()

    def test_sucesso_salva_a_analise_e_conclui(self, analisar):
        analisar.return_value = ANALISE_VALIDA

        self.executar()

        self.assertEqual(self.avaliacao.status, StatusAvaliacao.CONCLUIDA)
        self.assertEqual(self.aberta.feedback_ia, ANALISE_VALIDA)

    def test_falha_transitoria_e_retentada_ate_dar_certo(self, analisar):
        analisar.side_effect = [llm.FalhaInferencia('timeout'), llm.FalhaInferencia('json'), ANALISE_VALIDA]

        self.executar()

        self.assertEqual(self.avaliacao.status, StatusAvaliacao.CONCLUIDA)
        self.assertEqual(self.aberta.tentativas_ia, 2)

    def test_falha_persistente_marca_erro_de_processamento(self, analisar):
        analisar.side_effect = llm.FalhaInferencia('ollama fora do ar')

        self.executar()

        self.assertEqual(self.avaliacao.status, StatusAvaliacao.ERRO_PROCESSAMENTO)
        self.assertEqual(analisar.call_count, 4)  # 1 tentativa + 3 retentativas
        self.assertIsNone(self.aberta.feedback_ia)

    def test_resposta_ja_analisada_nao_e_reenviada(self, analisar):
        self.aberta.feedback_ia = ANALISE_VALIDA
        self.aberta.save()

        self.executar()

        analisar.assert_not_called()
        self.assertEqual(self.avaliacao.status, StatusAvaliacao.CONCLUIDA)
