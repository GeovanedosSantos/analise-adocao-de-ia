from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TokenEmpresaSerializer(TokenObtainPairSerializer):
    """Inclui a empresa no token. As views usam a empresa do usuário no banco, não a do token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['empresa_id'] = str(user.empresa_id) if user.empresa_id else None
        return token
