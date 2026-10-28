import re

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from .fabricas import SENHA, criar_empresa, criar_usuario

ESQUECI = '/api/v1/auth/senha/esqueci/'
REDEFINIR = '/api/v1/auth/senha/redefinir/'


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', FRONTEND_URL='https://app.exemplo')
class RecuperarSenhaTests(APITestCase):
    def setUp(self):
        cache.clear()  # o limite de taxa da recuperação de senha fica no cache
        self.usuario = criar_usuario(criar_empresa(), username='ana')
        self.usuario.email = 'ana@empresa.com'
        self.usuario.save()

    def link_enviado(self):
        uid, token = re.search(r'uid=([^&\s]+)&token=(\S+)', mail.outbox[-1].body).groups()
        return uid, token

    def test_envia_link_para_o_email_cadastrado(self):
        resposta = self.client.post(ESQUECI, {'email': 'ANA@empresa.com'})

        self.assertEqual(resposta.status_code, 204)
        self.assertEqual(mail.outbox[0].to, ['ana@empresa.com'])
        self.assertIn('https://app.exemplo/redefinir-senha?uid=', mail.outbox[0].body)

    def test_email_desconhecido_responde_igual_e_nao_envia_nada(self):
        resposta = self.client.post(ESQUECI, {'email': 'ninguem@empresa.com'})

        self.assertEqual(resposta.status_code, 204)
        self.assertEqual(mail.outbox, [])

    def test_link_redefine_a_senha_uma_vez_so(self):
        self.client.post(ESQUECI, {'email': 'ana@empresa.com'})
        uid, token = self.link_enviado()

        primeira = self.client.post(REDEFINIR, {'uid': uid, 'token': token, 'nova_senha': 'Nova-senha-forte-42'})
        segunda = self.client.post(REDEFINIR, {'uid': uid, 'token': token, 'nova_senha': 'Outra-senha-forte-42'})

        self.assertEqual((primeira.status_code, segunda.status_code), (204, 400))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Nova-senha-forte-42'))

    def test_recusa_senha_fraca_e_token_invalido(self):
        self.client.post(ESQUECI, {'email': 'ana@empresa.com'})
        uid, token = self.link_enviado()

        fraca = self.client.post(REDEFINIR, {'uid': uid, 'token': token, 'nova_senha': '123'})
        invalido = self.client.post(REDEFINIR, {'uid': uid, 'token': 'abc-123', 'nova_senha': 'Nova-senha-forte-42'})

        self.assertEqual((fraca.status_code, invalido.status_code), (400, 400))
        self.assertIn('nova_senha', fraca.data)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(SENHA))

    def test_limite_de_tentativas(self):
        respostas = [self.client.post(ESQUECI, {'email': 'x@x.com'}).status_code for _ in range(6)]

        self.assertEqual(respostas[-1], 429)
