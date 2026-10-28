from django.db import connection
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.avaliacoes.models import Avaliacao, StatusAvaliacao
from apps.contas.tenancy import definir_empresa_rls, ignorar_rls, transacao_da_empresa
from apps.avaliacoes.services import calcular_pontuacao, selecionar_recomendacoes
from apps.contas.tests.fabricas import criar_empresa
from apps.questionarios.tests.fabricas import criar_questionario, perguntas
from apps.recomendacoes.tests.fabricas import criar_recomendacao

from .fabricas import criar_avaliacao, responder_objetivas


class RowLevelSecurityTests(TestCase):
    """O Postgres ignora RLS para superusuários, então os testes assumem um papel comum."""

    def setUp(self):
        questionario = criar_questionario()
        self.empresa_a, self.empresa_b = criar_empresa('A'), criar_empresa('B')
        self.avaliacao_a = criar_avaliacao(self.empresa_a, questionario)
        responder_objetivas(self.avaliacao_a, [5, 1, 5])
        calcular_pontuacao(self.avaliacao_a)
        criar_recomendacao('dados-1', 'dados')
        selecionar_recomendacoes(self.avaliacao_a)
        criar_avaliacao(self.empresa_b, questionario)
        with connection.cursor() as cursor:
            cursor.execute('CREATE ROLE rls_teste NOLOGIN')
            cursor.execute('GRANT SELECT ON ALL TABLES IN SCHEMA public TO rls_teste')
            cursor.execute('SET LOCAL ROLE rls_teste')

    def test_sessao_so_enxerga_linhas_da_propria_empresa(self):
        definir_empresa_rls(self.empresa_a.id)

        self.assertEqual(list(Avaliacao.objects.values_list('empresa_id', flat=True)), [self.empresa_a.id])
        self.assertEqual(self.avaliacao_a.respostas.count(), 3)
        self.assertEqual(self.avaliacao_a.recomendacoes.count(), 1)

    def test_sem_empresa_definida_nada_e_visivel(self):
        self.assertFalse(Avaliacao.objects.exists())

    def test_filhas_de_outra_empresa_ficam_invisiveis(self):
        definir_empresa_rls(self.empresa_b.id)

        self.assertEqual(self.avaliacao_a.respostas.count(), 0)
        self.assertEqual(self.avaliacao_a.recomendacoes.count(), 0)

    def test_bypass_explicito_para_workers_e_admin(self):
        with ignorar_rls():
            self.assertEqual(Avaliacao.objects.count(), 2)
        self.assertFalse(Avaliacao.objects.exists())


class VersaoTravadaTests(TestCase):
    def setUp(self):
        self.questionario = criar_questionario()
        self.avaliacao = criar_avaliacao(criar_empresa(), self.questionario)
        self.pergunta = perguntas(self.questionario)[0]

    def submeter(self):
        self.avaliacao.status = StatusAvaliacao.CONCLUIDA
        self.avaliacao.save()

    def test_pergunta_pode_ser_editada_enquanto_so_ha_rascunhos(self):
        self.pergunta.texto = 'Novo texto'
        self.pergunta.save()

    def test_pergunta_de_versao_ja_respondida_nao_pode_mudar(self):
        self.submeter()
        self.pergunta.peso = 10

        with self.assertRaises(ValidationError):
            self.pergunta.save()

    def test_codigo_da_dimensao_de_versao_ja_respondida_nao_pode_mudar(self):
        self.submeter()
        dimensao = self.pergunta.dimensao
        dimensao.codigo = 'outro'

        with self.assertRaises(ValidationError):
            dimensao.save()

    def test_inativar_pergunta_continua_permitido(self):
        self.submeter()
        self.pergunta.ativa = False

        self.pergunta.save()

    def test_versao_com_avaliacoes_nao_pode_ser_apagada(self):
        with self.assertRaises(ProtectedError):
            self.questionario.delete()


class WorkerComTenantTests(TestCase):
    """Os workers rodam com o tenant da avaliação em vez de ignorar o RLS (seção 5.3)."""

    def test_transacao_da_empresa_so_enxerga_a_propria_empresa(self):
        questionario = criar_questionario()
        empresa_a, empresa_b = criar_empresa('A'), criar_empresa('B')
        criar_avaliacao(empresa_a, questionario)
        criar_avaliacao(empresa_b, questionario)
        with connection.cursor() as cursor:
            cursor.execute('CREATE ROLE rls_worker NOLOGIN')
            cursor.execute('GRANT SELECT ON ALL TABLES IN SCHEMA public TO rls_worker')
            cursor.execute('SET LOCAL ROLE rls_worker')

        with transacao_da_empresa(empresa_a.id):
            visiveis = list(Avaliacao.objects.values_list('empresa_id', flat=True))

        self.assertEqual(visiveis, [empresa_a.id])
