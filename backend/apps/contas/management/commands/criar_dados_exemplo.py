from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.contas.models import Empresa, Usuario


class Command(BaseCommand):
    help = 'Cria empresa e usuário "demo" e carrega o modelo de prontidão e o catálogo para desenvolvimento local.'

    def add_arguments(self, parser):
        parser.add_argument('--senha', required=True, help='Senha do usuário demo.')

    @transaction.atomic
    def handle(self, *args, senha, **options):
        empresa, _ = Empresa.objects.get_or_create(nome='Empresa Exemplo', defaults={'setor': 'Varejo'})
        usuario, _ = Usuario.objects.get_or_create(
            username='demo', defaults={'empresa': empresa, 'email': 'demo@example.com'},
        )
        usuario.set_password(senha)
        usuario.save()
        call_command('carregar_modelo_prontidao', stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('Dados de exemplo prontos. Usuário: demo'))
