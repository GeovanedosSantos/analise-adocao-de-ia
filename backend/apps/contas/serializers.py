from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as SenhaFraca
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario


class TokenEmpresaSerializer(TokenObtainPairSerializer):
    """Inclui a empresa no token. As views usam a empresa do usuário no banco, não a do token.

    Aceita o nome de usuário ou o e-mail (contas criadas pelo cadastro usam o e-mail para entrar).
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['empresa_id'] = str(user.empresa_id) if user.empresa_id else None
        return token

    def validate(self, attrs):
        identificador = attrs.get(self.username_field, '')
        if '@' in identificador and not Usuario.objects.filter(username=identificador).exists():
            # Só troca quando o e-mail aponta para exatamente uma conta; senão o login falha normalmente
            donos = list(Usuario.objects.filter(email__iexact=identificador).values_list('username', flat=True)[:2])
            if len(donos) == 1:
                attrs[self.username_field] = donos[0]
        return super().validate(attrs)


MENSAGENS_OBRIGATORIO = {'required': 'Preencha este campo.', 'blank': 'Preencha este campo.'}


def _texto(rotulo, maximo):
    return serializers.CharField(
        max_length=maximo,
        trim_whitespace=True,
        error_messages={**MENSAGENS_OBRIGATORIO, 'max_length': f'{rotulo} pode ter no máximo {maximo} caracteres.'},
    )


class EmpresaNovaSerializer(serializers.Serializer):
    empresa_nome = _texto('O nome da empresa', 255)
    empresa_setor = _texto('O setor', 100)


class CadastroSerializer(EmpresaNovaSerializer):
    nome = _texto('O nome', 150)
    email = serializers.EmailField(
        max_length=254,
        error_messages={**MENSAGENS_OBRIGATORIO, 'invalid': 'Informe um e-mail válido.'},
    )
    senha = serializers.CharField(write_only=True, trim_whitespace=False, error_messages=MENSAGENS_OBRIGATORIO)

    def validate_email(self, valor):
        valor = valor.lower()
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError('Já existe uma conta com este e-mail. Entre ou recupere a senha.')
        return valor

    def validate(self, dados):
        # Os validadores do Django comparam a senha com nome e e-mail, então rodam com o usuário montado
        provisorio = Usuario(username=dados['email'], email=dados['email'], first_name=dados['nome'])
        try:
            validate_password(dados['senha'], provisorio)
        except SenhaFraca as erro:
            raise serializers.ValidationError({'senha': erro.messages})
        return dados


class GoogleEntrarSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2048)
    code_verifier = serializers.CharField(min_length=43, max_length=128)


class GoogleConcluirSerializer(EmpresaNovaSerializer):
    token_cadastro = serializers.CharField(max_length=2048)
