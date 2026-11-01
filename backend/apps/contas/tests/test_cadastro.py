import base64
import json
import time
from unittest import mock

import requests
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.contas import cadastro
from apps.contas.models import ContaGoogle, Empresa, Usuario

from .fabricas import SENHA, criar_empresa, criar_usuario

DADOS = {
    'nome': 'Marina Costa',
    'email': 'Marina@Exemplo.com.br',
    'senha': 'horta-azul-de-julho',
    'empresa_nome': 'Padaria Aurora',
    'empresa_setor': 'Alimentação',
}


class CadastroTests(APITestCase):
    def setUp(self):
        cache.clear()  # o limite de taxa do cadastro fica no cache

    def test_cria_empresa_e_usuario_e_ja_entra(self):
        resposta = self.client.post('/api/v1/auth/cadastro/', DADOS)

        self.assertEqual(resposta.status_code, 201)
        usuario = Usuario.objects.get(email='marina@exemplo.com.br')
        self.assertEqual(usuario.first_name, 'Marina Costa')
        self.assertEqual(usuario.empresa.nome, 'Padaria Aurora')
        self.assertEqual(usuario.empresa.setor, 'Alimentação')
        self.assertEqual(AccessToken(resposta.data['access'])['empresa_id'], str(usuario.empresa_id))

    def test_conta_nova_nao_tem_acesso_administrativo(self):
        self.client.post('/api/v1/auth/cadastro/', {**DADOS, 'is_staff': True, 'is_superuser': True})

        usuario = Usuario.objects.get(email='marina@exemplo.com.br')
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertFalse(usuario.user_permissions.exists())

    def test_senha_fica_so_como_hash(self):
        self.client.post('/api/v1/auth/cadastro/', DADOS)

        usuario = Usuario.objects.get(email='marina@exemplo.com.br')
        self.assertNotIn(DADOS['senha'], usuario.password)
        self.assertTrue(usuario.check_password(DADOS['senha']))

    def test_conta_nova_acessa_dados_da_propria_empresa(self):
        token = self.client.post('/api/v1/auth/cadastro/', DADOS).data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(self.client.get('/api/v1/avaliacoes/').status_code, 200)

    def test_entra_depois_com_o_email(self):
        self.client.post('/api/v1/auth/cadastro/', DADOS)

        resposta = self.client.post('/api/v1/auth/token/', {'username': 'MARINA@exemplo.com.br', 'password': DADOS['senha']})

        self.assertEqual(resposta.status_code, 200)

    def test_email_repetido_e_recusado_sem_criar_empresa(self):
        existente = criar_usuario(criar_empresa())
        existente.email = 'marina@exemplo.com.br'
        existente.save()

        resposta = self.client.post('/api/v1/auth/cadastro/', DADOS)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn('email', resposta.data)
        self.assertFalse(Empresa.objects.filter(nome='Padaria Aurora').exists())

    def test_senha_fraca_ou_parecida_com_o_email_e_recusada(self):
        for senha in ['12345678', 'curta', 'marina@exemplo']:
            with self.subTest(senha=senha):
                cache.clear()
                resposta = self.client.post('/api/v1/auth/cadastro/', {**DADOS, 'senha': senha})
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('senha', resposta.data)
        self.assertFalse(Usuario.objects.filter(email='marina@exemplo.com.br').exists())

    def test_campos_obrigatorios_tem_mensagem_em_portugues(self):
        resposta = self.client.post('/api/v1/auth/cadastro/', {})

        self.assertEqual(resposta.status_code, 400)
        for campo in DADOS:
            self.assertEqual(resposta.data[campo], ['Preencha este campo.'])

    def test_email_invalido(self):
        resposta = self.client.post('/api/v1/auth/cadastro/', {**DADOS, 'email': 'nao-e-email'})

        self.assertEqual(resposta.data['email'], ['Informe um e-mail válido.'])

    def test_limite_de_tentativas(self):
        for _ in range(5):
            self.client.post('/api/v1/auth/cadastro/', {})

        self.assertEqual(self.client.post('/api/v1/auth/cadastro/', {}).status_code, 429)


class LoginPorEmailTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_email_compartilhado_por_duas_contas_nao_entra(self):
        for nome in ['ana', 'ana2']:
            usuario = criar_usuario(criar_empresa(), username=nome)
            usuario.email = 'ana@exemplo.com'
            usuario.save()

        resposta = self.client.post('/api/v1/auth/token/', {'username': 'ana@exemplo.com', 'password': SENHA})

        self.assertEqual(resposta.status_code, 401)

    def test_nome_de_usuario_continua_funcionando(self):
        criar_usuario(criar_empresa(), username='demo')

        resposta = self.client.post('/api/v1/auth/token/', {'username': 'demo', 'password': SENHA})

        self.assertEqual(resposta.status_code, 200)


# Google ---------------------------------------------------------------------------------------

CLIENT_ID = 'cliente-teste.apps.googleusercontent.com'


def id_token(**declaracoes):
    padrao = {
        'iss': 'https://accounts.google.com',
        'aud': CLIENT_ID,
        'exp': int(time.time()) + 300,
        'sub': '1122334455',
        'email': 'Lia@gmail.com',
        'email_verified': True,
        'name': 'Lia Souza',
    }
    carga = base64.urlsafe_b64encode(json.dumps({**padrao, **declaracoes}).encode()).decode().rstrip('=')
    return f'cabecalho.{carga}.assinatura'


def resposta_google(status=200, **declaracoes):
    falsa = mock.Mock(status_code=status)
    falsa.json.return_value = {'id_token': id_token(**declaracoes)} if status == 200 else {'error': 'invalid_grant'}
    return falsa


CODIGO = {'code': 'codigo-do-google', 'code_verifier': 'v' * 43}


@override_settings(
    GOOGLE_CLIENT_ID=CLIENT_ID,
    GOOGLE_CLIENT_SECRET='segredo-teste',
    GOOGLE_REDIRECT_URI='https://app.exemplo/entrar/google/retorno',
)
class GoogleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def entrar(self, resposta=None, **declaracoes):
        with mock.patch.object(cadastro.requests, 'post', return_value=resposta or resposta_google(**declaracoes)) as post:
            return self.client.post('/api/v1/auth/google/', CODIGO), post

    def test_config_expoe_so_o_client_id(self):
        resposta = self.client.get('/api/v1/auth/google/config/')

        self.assertEqual(resposta.data, {
            'habilitado': True,
            'client_id': CLIENT_ID,
            'redirect_uri': 'https://app.exemplo/entrar/google/retorno',
        })
        self.assertNotIn('segredo-teste', json.dumps(resposta.data))

    @override_settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET='')
    def test_sem_credenciais_fica_desligado(self):
        self.assertEqual(self.client.get('/api/v1/auth/google/config/').data, {'habilitado': False})
        self.assertEqual(self.client.post('/api/v1/auth/google/', CODIGO).status_code, 503)

    def test_troca_o_codigo_com_pkce_e_segredo_no_servidor(self):
        _, post = self.entrar()

        dados = post.call_args.kwargs['data']
        self.assertEqual(dados['code_verifier'], CODIGO['code_verifier'])
        self.assertEqual(dados['client_secret'], 'segredo-teste')
        self.assertEqual(dados['redirect_uri'], 'https://app.exemplo/entrar/google/retorno')

    def test_conta_nova_pede_empresa_e_conclui(self):
        resposta, _ = self.entrar()

        self.assertTrue(resposta.data['cadastro_pendente'])
        self.assertEqual(resposta.data['email'], 'lia@gmail.com')
        self.assertFalse(Usuario.objects.filter(email='lia@gmail.com').exists())

        concluido = self.client.post('/api/v1/auth/google/concluir/', {
            'token_cadastro': resposta.data['token_cadastro'],
            'empresa_nome': 'Lia Contábil',
            'empresa_setor': 'Serviços',
        })

        self.assertEqual(concluido.status_code, 201)
        usuario = Usuario.objects.get(email='lia@gmail.com')
        self.assertEqual(usuario.conta_google.sub, '1122334455')
        self.assertEqual(usuario.empresa.nome, 'Lia Contábil')
        self.assertFalse(usuario.has_usable_password())
        self.assertFalse(usuario.is_staff)

    def test_conta_vinculada_entra_direto(self):
        usuario = criar_usuario(criar_empresa())
        ContaGoogle.objects.create(usuario=usuario, sub='1122334455', email='lia@gmail.com')

        resposta, _ = self.entrar()

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(AccessToken(resposta.data['access'])['user_id'], str(usuario.pk))

    def test_email_de_conta_existente_nao_e_vinculado(self):
        existente = criar_usuario(criar_empresa())
        existente.email = 'lia@gmail.com'
        existente.save()

        resposta, _ = self.entrar()

        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(resposta.data['codigo'], 'email_em_uso')
        self.assertNotIn('access', resposta.data)
        self.assertFalse(ContaGoogle.objects.exists())

    def test_conta_desativada_nao_entra(self):
        usuario = criar_usuario(criar_empresa())
        usuario.is_active = False
        usuario.save()
        ContaGoogle.objects.create(usuario=usuario, sub='1122334455', email='lia@gmail.com')

        resposta, _ = self.entrar()

        self.assertEqual(resposta.status_code, 403)

    def test_respostas_invalidas_do_google_sao_recusadas(self):
        casos = {
            'outro público': {'aud': 'outro-app'},
            'outro emissor': {'iss': 'https://falso.exemplo'},
            'expirado': {'exp': int(time.time()) - 10},
            'e-mail não confirmado': {'email_verified': False},
            'sem e-mail': {'email': ''},
        }
        for caso, declaracoes in casos.items():
            with self.subTest(caso):
                cache.clear()
                resposta, _ = self.entrar(**declaracoes)
                self.assertEqual(resposta.status_code, 400)
                self.assertNotIn('access', resposta.data)
                self.assertNotIn('token_cadastro', resposta.data)

    def test_codigo_recusado_pelo_google(self):
        resposta, _ = self.entrar(resposta=resposta_google(status=400))

        self.assertEqual(resposta.status_code, 400)

    def test_falha_de_rede(self):
        with mock.patch.object(cadastro.requests, 'post', side_effect=requests.ConnectionError):
            resposta = self.client.post('/api/v1/auth/google/', CODIGO)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn('Google', resposta.data['detail'])

    def test_token_de_cadastro_adulterado_ou_vencido(self):
        valido = cadastro.gerar_token_cadastro('1', 'x@gmail.com', 'X')
        for token in [valido + 'a', 'qualquer-coisa']:
            with self.subTest(token=token):
                resposta = self.client.post('/api/v1/auth/google/concluir/', {
                    'token_cadastro': token, 'empresa_nome': 'E', 'empresa_setor': 'S',
                })
                self.assertEqual(resposta.status_code, 400)

        with mock.patch.object(cadastro, 'VALIDADE_CADASTRO_GOOGLE', -1):
            resposta = self.client.post('/api/v1/auth/google/concluir/', {
                'token_cadastro': valido, 'empresa_nome': 'E', 'empresa_setor': 'S',
            })
        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(Usuario.objects.filter(email='x@gmail.com').exists())

    def test_concluir_duas_vezes_nao_duplica(self):
        token = cadastro.gerar_token_cadastro('1', 'x@gmail.com', 'X')
        corpo = {'token_cadastro': token, 'empresa_nome': 'E', 'empresa_setor': 'S'}

        self.assertEqual(self.client.post('/api/v1/auth/google/concluir/', corpo).status_code, 201)
        self.assertEqual(self.client.post('/api/v1/auth/google/concluir/', corpo).status_code, 409)
        self.assertEqual(Usuario.objects.filter(email='x@gmail.com').count(), 1)
