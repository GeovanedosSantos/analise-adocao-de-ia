"""Login e recuperação de senha (UC01)."""

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

from .models import Usuario

logger = logging.getLogger(__name__)


class EntrarView(TokenObtainPairView):
    throttle_scope = 'login'


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
