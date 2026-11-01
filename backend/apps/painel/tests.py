from django.core.cache import cache
from django.test import TestCase

from apps.contas.models import Usuario

SENHA = 'senha-de-teste-123'


class PainelTests(TestCase):
    def test_login_do_painel_usa_a_identidade_do_produto(self):
        resposta = self.client.get('/admin/login/')

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'painel/painel.css')
        self.assertContains(resposta, 'Entrar no painel')

    def test_indice_abre_para_superusuario_com_todos_os_modelos(self):
        admin = Usuario.objects.create_superuser('raiz', 'raiz@exemplo.com', SENHA)
        self.client.force_login(admin)

        resposta = self.client.get('/admin/')

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Painel administrativo')
        for modelo in ['contas/usuario', 'contas/empresa', 'questionarios/questionario', 'recomendacoes/recomendacao']:
            self.assertContains(resposta, f'/admin/{modelo}/')

    def test_conta_criada_pelo_cadastro_nao_entra_no_painel(self):
        cache.clear()
        self.client.post('/api/v1/auth/cadastro/', {
            'nome': 'Ana', 'email': 'ana@exemplo.com', 'senha': 'horta-azul-de-julho',
            'empresa_nome': 'Ana ME', 'empresa_setor': 'Serviços',
        })
        self.client.force_login(Usuario.objects.get(email='ana@exemplo.com'))

        resposta = self.client.get('/admin/')

        self.assertRedirects(resposta, '/admin/login/?next=/admin/')
