from apps.contas.models import Empresa, Usuario

SENHA = 'senha-de-teste-123'


def criar_empresa(nome='Empresa A', setor='Varejo'):
    return Empresa.objects.create(nome=nome, setor=setor)


def criar_usuario(empresa, username=None):
    username = username or f'usuario-{Usuario.objects.count() + 1}'
    return Usuario.objects.create_user(username=username, password=SENHA, empresa=empresa)
