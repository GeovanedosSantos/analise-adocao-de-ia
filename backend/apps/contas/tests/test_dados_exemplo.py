from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.contas.models import Usuario
from apps.questionarios.models import Questionario


class DadosExemploTests(TestCase):
    def rodar(self):
        call_command('criar_dados_exemplo', '--senha', 'senha-demo-123', stdout=StringIO())

    def test_cria_usuario_da_empresa_e_questionario_publicado(self):
        self.rodar()

        usuario = Usuario.objects.get(username='demo')
        self.assertIsNotNone(usuario.empresa)
        self.assertTrue(usuario.check_password('senha-demo-123'))
        ativo = Questionario.objects.get(ativo=True)
        self.assertTrue(ativo.dimensoes.filter(perguntas__tipo='DISSERTATIVA').exists())

    def test_pode_rodar_mais_de_uma_vez(self):
        self.rodar()
        self.rodar()

        self.assertEqual(Usuario.objects.filter(username='demo').count(), 1)
        self.assertEqual(Questionario.objects.count(), 1)
