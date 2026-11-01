"""Cadastro de novas contas: por e-mail e senha ou pela conta Google (OpenID Connect).

Cada cadastro cria uma empresa nova e o primeiro usuário dela. O usuário criado nunca recebe
acesso ao painel administrativo (is_staff e is_superuser ficam falsos).
"""

import base64
import json
import logging
import time

import requests
from django.conf import settings
from django.core import signing
from django.db import transaction

from .models import ContaGoogle, Empresa, Usuario
from .serializers import TokenEmpresaSerializer

logger = logging.getLogger(__name__)

URL_TOKEN_GOOGLE = 'https://oauth2.googleapis.com/token'
EMISSORES_GOOGLE = {'https://accounts.google.com', 'accounts.google.com'}
SAL_CADASTRO_GOOGLE = 'contas.cadastro-google'
# Tempo para a pessoa informar a empresa depois de voltar do Google
VALIDADE_CADASTRO_GOOGLE = 15 * 60


class ErroGoogle(Exception):
    """Falha ao validar o retorno do Google. A mensagem pode ser mostrada à pessoa."""


def email_em_uso(email):
    return Usuario.objects.filter(email__iexact=email).exists()


def _username_livre(email):
    """Usa o e-mail como nome de usuário; se já existir (caso raro), acrescenta um número."""
    base = email.lower()[:140]
    candidato, n = base, 1
    while Usuario.objects.filter(username__iexact=candidato).exists():
        n += 1
        candidato = f'{base}-{n}'
    return candidato


@transaction.atomic
def criar_conta(*, nome, email, empresa_nome, empresa_setor, senha=None):
    """Cria a empresa e o usuário. Sem senha (cadastro pelo Google), a senha fica inutilizável."""
    empresa = Empresa.objects.create(nome=empresa_nome, setor=empresa_setor)
    usuario = Usuario(
        username=_username_livre(email),
        email=email.lower(),
        first_name=nome[:150],
        empresa=empresa,
        is_staff=False,
        is_superuser=False,
    )
    if senha:
        usuario.set_password(senha)
    else:
        usuario.set_unusable_password()
    usuario.save()
    logger.info('Conta criada: usuário %s, empresa %s', usuario.pk, empresa.pk)
    return usuario


def tokens_para(usuario):
    """Mesmos tokens do login (com a empresa no token de acesso)."""
    refresh = TokenEmpresaSerializer.get_token(usuario)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# Google ---------------------------------------------------------------------------------------


def google_configurado():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def _ler_id_token(id_token):
    """Lê as declarações do ID token.

    O token chega direto do endpoint de token do Google, por TLS e autenticado com o segredo do
    cliente; nesse caso o OpenID Connect Core (seção 3.1.3.7, item 6) permite validar pelo TLS em
    vez da assinatura. As declarações (emissor, público, validade) são conferidas abaixo.
    """
    try:
        carga = id_token.split('.')[1]
        carga += '=' * (-len(carga) % 4)
        return json.loads(base64.urlsafe_b64decode(carga))
    except (IndexError, ValueError):
        raise ErroGoogle('O Google devolveu uma resposta inválida.')


def identidade_google(code, code_verifier):
    """Troca o código de autorização pelo ID token e devolve (sub, e-mail, nome)."""
    try:
        resposta = requests.post(
            URL_TOKEN_GOOGLE,
            data={
                'code': code,
                'code_verifier': code_verifier,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.warning('Falha de rede ao falar com o Google')
        raise ErroGoogle('Não foi possível falar com o Google agora. Tente de novo.')

    if resposta.status_code != 200:
        # Código expirado, já usado ou redirect_uri diferente do cadastrado no Google
        logger.warning('Google recusou a troca do código: %s', resposta.status_code)
        raise ErroGoogle('O acesso pelo Google expirou ou foi recusado. Tente de novo.')

    id_token = resposta.json().get('id_token')
    if not id_token:
        raise ErroGoogle('O Google devolveu uma resposta inválida.')
    dados = _ler_id_token(id_token)

    if dados.get('iss') not in EMISSORES_GOOGLE or dados.get('aud') != settings.GOOGLE_CLIENT_ID:
        raise ErroGoogle('O Google devolveu uma resposta inválida.')
    if int(dados.get('exp', 0)) < time.time():
        raise ErroGoogle('O acesso pelo Google expirou. Tente de novo.')
    if not dados.get('sub') or not dados.get('email'):
        raise ErroGoogle('O Google não informou o e-mail da conta.')
    if dados.get('email_verified') is not True:
        raise ErroGoogle('Esse e-mail ainda não foi confirmado no Google.')

    return dados['sub'], dados['email'].lower(), dados.get('name') or ''


def gerar_token_cadastro(sub, email, nome):
    return signing.dumps({'sub': sub, 'email': email, 'nome': nome}, salt=SAL_CADASTRO_GOOGLE)


def ler_token_cadastro(token):
    """Devolve os dados assinados ou None se o token for inválido ou tiver expirado."""
    try:
        return signing.loads(token, salt=SAL_CADASTRO_GOOGLE, max_age=VALIDADE_CADASTRO_GOOGLE)
    except signing.BadSignature:
        return None


@transaction.atomic
def criar_conta_google(*, sub, email, nome, empresa_nome, empresa_setor):
    usuario = criar_conta(nome=nome, email=email, empresa_nome=empresa_nome, empresa_setor=empresa_setor)
    ContaGoogle.objects.create(usuario=usuario, sub=sub, email=email)
    return usuario

