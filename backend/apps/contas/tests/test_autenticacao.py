from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .fabricas import SENHA, criar_empresa, criar_usuario


class TokenJwtTests(APITestCase):
    def test_token_carrega_empresa_do_usuario(self):
        empresa = criar_empresa()
        usuario = criar_usuario(empresa)

        resposta = self.client.post('/api/v1/auth/token/', {'username': usuario.username, 'password': SENHA})

        self.assertEqual(resposta.status_code, 200)
        token = AccessToken(resposta.data['access'])
        self.assertEqual(token['empresa_id'], str(empresa.id))

    def test_credenciais_invalidas_sao_recusadas(self):
        criar_usuario(criar_empresa(), username='ana')

        resposta = self.client.post('/api/v1/auth/token/', {'username': 'ana', 'password': 'errada'})

        self.assertEqual(resposta.status_code, 401)


class UsuarioSemEmpresaTests(APITestCase):
    def test_usuario_sem_empresa_nao_acessa_dados_de_tenant(self):
        admin = get_user_model().objects.create_user(username='admin', password=SENHA)
        self.client.force_authenticate(admin)

        resposta = self.client.get('/api/v1/avaliacoes/')

        self.assertEqual(resposta.status_code, 403)

    def test_requisicao_sem_token_e_recusada(self):
        resposta = self.client.get('/api/v1/avaliacoes/')

        self.assertEqual(resposta.status_code, 401)
