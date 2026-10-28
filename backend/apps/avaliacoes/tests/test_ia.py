import json
from unittest import mock

import requests
from django.test import TestCase, override_settings

from apps.avaliacoes import llm
from apps.avaliacoes.models import StatusAvaliacao
from apps.avaliacoes.services import calcular_pontuacao, selecionar_recomendacoes
from apps.avaliacoes.tasks import processar_ia
from apps.contas.tests.fabricas import criar_empresa
from apps.questionarios.tests.fabricas import criar_questionario
from apps.recomendacoes.tests.fabricas import criar_recomendacao

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


ACOES = [{'codigo': 'a'}, {'codigo': 'b'}, {'codigo': 'c'}]


@mock.patch('apps.avaliacoes.llm.requests.post')
class OrdenarRecomendacoesTests(TestCase):
    def ordenar(self):
        dimensoes = {'dados': {'nota': 25.0, 'peso': 2}, 'pessoas': {'nota': 100.0, 'peso': 1}}
        return llm.ordenar_recomendacoes(50.0, dimensoes, ACOES, [{'dimensao': 'dados', 'analise': 'Planilhas soltas.', 'riscos': []}])

    def test_retorna_a_nova_ordem_e_envia_as_notas_no_prompt(self, post):
        post.return_value = resposta_ollama(json.dumps({'ordem': ['c', 'a', 'b']}))

        self.assertEqual(self.ordenar(), ['c', 'a', 'b'])
        prompt = post.call_args.kwargs['json']['prompt']
        self.assertIn('"dados": {"nota": 25.0, "peso": 2}', prompt)
        self.assertIn('Planilhas soltas.', prompt)

    def test_rejeita_ordem_que_nao_e_permutacao_dos_codigos(self, post):
        for ordem in (['a', 'b'], ['a', 'a', 'b'], ['a', 'b', 'x'], ['a', 'b', 'c', 'c']):
            with self.subTest(ordem=ordem):
                post.return_value = resposta_ollama(json.dumps({'ordem': ordem}))
                with self.assertRaises(llm.FalhaInferencia):
                    self.ordenar()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, IA_MAX_TENTATIVAS=3)
@mock.patch('apps.avaliacoes.tasks.llm.analisar_resposta')
class ProcessarRespostasAbertasTests(TestCase):
    """Sem catálogo cadastrado: o plano de ação fica vazio e só as respostas abertas vão para a IA."""

    def setUp(self):
        self.avaliacao = criar_avaliacao(criar_empresa(), criar_questionario(), status=StatusAvaliacao.PROCESSANDO_IA)
        responder_objetivas(self.avaliacao, [5, 1, 5])
        responder_dissertativas(self.avaliacao)
        self.aberta = self.avaliacao.respostas.get(texto_aberto__gt='')

    def executar(self):
        processar_ia.apply(args=[str(self.avaliacao.id), str(self.avaliacao.empresa_id)])
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


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, IA_MAX_TENTATIVAS=2, TOTAL_RECOMENDACOES=2, IA_MAX_CANDIDATAS=30)
@mock.patch('apps.avaliacoes.tasks.llm.ordenar_recomendacoes')
@mock.patch('apps.avaliacoes.tasks.llm.analisar_resposta', return_value=ANALISE_VALIDA)
class RanquearPlanoDeAcaoTests(TestCase):
    """Três recomendações aplicáveis e plano de 2: a IA ranqueia as três e só as 2 primeiras ficam (UC12)."""

    def setUp(self):
        self.avaliacao = criar_avaliacao(criar_empresa(), criar_questionario(), status=StatusAvaliacao.PROCESSANDO_IA)
        responder_objetivas(self.avaliacao, [5, 1, 5])
        responder_dissertativas(self.avaliacao)
        calcular_pontuacao(self.avaliacao)
        for codigo in ('a', 'b', 'c'):
            criar_recomendacao(codigo, 'dados', (0, 40))
        selecionar_recomendacoes(self.avaliacao)

    def executar(self):
        processar_ia.apply(args=[str(self.avaliacao.id), str(self.avaliacao.empresa_id)])
        self.avaliacao.refresh_from_db()
        return list(self.avaliacao.recomendacoes.values_list('recomendacao__codigo', flat=True))

    def test_antes_da_ia_vale_a_ordem_das_faixas(self, analisar, ordenar):
        self.assertEqual(list(self.avaliacao.recomendacoes.values_list('recomendacao__codigo', flat=True)), ['a', 'b'])

    def test_ia_ranqueia_todas_as_aplicaveis_com_notas_pesos_e_analises(self, analisar, ordenar):
        ordenar.return_value = ['c', 'a', 'b']

        self.assertEqual(self.executar(), ['c', 'a'])
        self.assertTrue(self.avaliacao.recomendacoes_ordenadas_ia)
        self.assertEqual(self.avaliacao.versao_prompts_ia, llm.VERSAO_PROMPTS)
        self.assertEqual(self.avaliacao.status, StatusAvaliacao.CONCLUIDA)
        nota_geral, dimensoes, acoes, analises = ordenar.call_args.args
        self.assertEqual(nota_geral, 50.0)
        self.assertEqual(dimensoes, {'dados': {'nota': 25.0, 'peso': 2.0}, 'pessoas': {'nota': 100.0, 'peso': 1.0}})
        self.assertEqual([a['codigo'] for a in acoes], ['a', 'b', 'c'])
        self.assertEqual(analises, [{'dimensao': 'dados', 'analise': 'Base de dados madura.', 'riscos': []}])

    def test_falha_persistente_marca_erro_e_mantem_a_ordem_das_faixas(self, analisar, ordenar):
        ordenar.side_effect = llm.FalhaInferencia('ollama fora do ar')

        self.assertEqual(self.executar(), ['a', 'b'])
        self.assertFalse(self.avaliacao.recomendacoes_ordenadas_ia)
        self.assertEqual(self.avaliacao.status, StatusAvaliacao.ERRO_PROCESSAMENTO)
        self.assertEqual(ordenar.call_count, 3)  # 1 tentativa + 2 retentativas

    def test_plano_ja_ranqueado_nao_e_reenviado(self, analisar, ordenar):
        self.avaliacao.recomendacoes_ordenadas_ia = True
        self.avaliacao.save()

        self.executar()

        ordenar.assert_not_called()
