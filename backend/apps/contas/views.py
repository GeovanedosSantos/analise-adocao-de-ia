"""Login, cadastro, entrada com Google e recuperação de senha (UC01)."""

import logging

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as SenhaFraca
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import cadastro
from .models import ContaGoogle, Usuario
from .serializers import CadastroSerializer, GoogleConcluirSerializer, GoogleEntrarSerializer

logger = logging.getLogger(__name__)


class EntrarView(TokenObtainPairView):
    throttle_scope = 'login'


EMAIL_EM_USO = (
    'Já existe uma conta com este e-mail. Entre com seu usuário ou e-mail e a senha. '
    'Se não lembrar a senha, use “Esqueci a minha senha”.'
)


class CadastroView(APIView):
    """Cria uma empresa e o primeiro usuário dela, e já devolve a sessão (mesmos tokens do login)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'cadastro'

    def post(self, request):
        dados = CadastroSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        d = dados.validated_data
        usuario = cadastro.criar_conta(
            nome=d['nome'], email=d['email'], senha=d['senha'],
            empresa_nome=d['empresa_nome'], empresa_setor=d['empresa_setor'],
        )
        return Response(cadastro.tokens_para(usuario), status=status.HTTP_201_CREATED)


class GoogleConfigView(APIView):
    """Diz ao front-end se a entrada com Google está ligada. Nunca expõe o segredo do cliente."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        if not cadastro.google_configurado():
            return Response({'habilitado': False})
        return Response({
            'habilitado': True,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        })


class GoogleEntrarView(APIView):
    """Recebe o código do Google (fluxo de autorização com PKCE) e entra, ou pede os dados da empresa.

    - Conta Google já vinculada: devolve os tokens.
    - E-mail já usado por outra conta: 409, sem vincular (evita que alguém tome uma conta
      cadastrada com o e-mail de outra pessoa).
    - Conta nova: devolve um token assinado para concluir o cadastro com a empresa.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        if not cadastro.google_configurado():
            return Response({'detail': 'A entrada com Google não está disponível.'}, status=503)
        dados = GoogleEntrarSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        try:
            sub, email, nome = cadastro.identidade_google(**dados.validated_data)
        except cadastro.ErroGoogle as erro:
            return Response({'detail': str(erro)}, status=400)

        vinculo = ContaGoogle.objects.select_related('usuario').filter(sub=sub).first()
        if vinculo is not None:
            if not vinculo.usuario.is_active:
                return Response({'detail': 'Esta conta está desativada.'}, status=403)
            return Response(cadastro.tokens_para(vinculo.usuario))

        if cadastro.email_em_uso(email):
            return Response({'codigo': 'email_em_uso', 'detail': EMAIL_EM_USO, 'email': email}, status=409)

        return Response({
            'cadastro_pendente': True,
            'token_cadastro': cadastro.gerar_token_cadastro(sub, email, nome),
            'email': email,
            'nome': nome,
        })


class GoogleConcluirView(APIView):
    """Segunda etapa do cadastro pelo Google: cria a empresa e a conta vinculada."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'cadastro'

    def post(self, request):
        dados = GoogleConcluirSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        identidade = cadastro.ler_token_cadastro(dados.validated_data['token_cadastro'])
        if identidade is None:
            return Response({'detail': 'O tempo para concluir o cadastro acabou. Entre com o Google de novo.'}, status=400)
        if ContaGoogle.objects.filter(sub=identidade['sub']).exists() or cadastro.email_em_uso(identidade['email']):
            return Response({'codigo': 'email_em_uso', 'detail': EMAIL_EM_USO, 'email': identidade['email']}, status=409)
        usuario = cadastro.criar_conta_google(
            sub=identidade['sub'],
            email=identidade['email'],
            nome=identidade['nome'],
            empresa_nome=dados.validated_data['empresa_nome'],
            empresa_setor=dados.validated_data['empresa_setor'],
        )
        return Response(cadastro.tokens_para(usuario), status=status.HTTP_201_CREATED)


class EsqueciSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RedefinirSenhaSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    nova_senha = serializers.CharField(write_only=True)


class EsqueciSenhaView(APIView):
    """Envia o link de redefinição (UC01 FA01).

    Responde 204 mesmo quando o e-mail não está cadastrado, para não revelar quem tem conta.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'senha'

    def post(self, request):
        dados = EsqueciSenhaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        for usuario in Usuario.objects.filter(email__iexact=dados.validated_data['email'], is_active=True):
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            link = f'{settings.FRONTEND_URL}/redefinir-senha?uid={uid}&token={token}'
            send_mail(
                'Redefinição de senha',
                f'Olá, {usuario.get_username()}.\n\nPara criar uma nova senha, abra o link abaixo:\n{link}\n\n'
                'Se você não pediu a redefinição, ignore este e-mail.',
                None,
                [usuario.email],
            )
            logger.info('Link de redefinição de senha enviado ao usuário %s', usuario.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RedefinirSenhaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'senha'

    def post(self, request):
        dados = RedefinirSenhaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        usuario = self._usuario(dados.validated_data['uid'])
        if usuario is None or not default_token_generator.check_token(usuario, dados.validated_data['token']):
            return Response({'detail': 'O link é inválido ou expirou. Peça um novo.'}, status=400)
        try:
            validate_password(dados.validated_data['nova_senha'], usuario)
        except SenhaFraca as erro:
            return Response({'nova_senha': erro.messages}, status=400)
        usuario.set_password(dados.validated_data['nova_senha'])
        usuario.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _usuario(self, uid):
        try:
            return Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
        except (ValueError, TypeError, OverflowError, Usuario.DoesNotExist):
            return None
