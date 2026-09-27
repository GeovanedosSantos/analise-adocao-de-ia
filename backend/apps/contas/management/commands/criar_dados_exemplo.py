from django.core.management.base import BaseCommand
from django.db import transaction

from apps.contas.models import Empresa, Usuario
from apps.questionarios.models import Dimensao, Pergunta, Questionario, TipoPergunta

VERSAO_EXEMPLO = '0.1-exemplo'

# Conteúdo provisório só para desenvolvimento: o modelo de avaliação real ainda será validado
DIMENSOES = [
    ('Estratégia', 1, [
        ('A liderança tem objetivos claros para o uso de IA?', TipoPergunta.OBJETIVA),
        ('Existe orçamento dedicado a iniciativas de IA?', TipoPergunta.OBJETIVA),
    ]),
    ('Dados', 2, [
        ('Os dados da empresa são catalogados e acessíveis?', TipoPergunta.OBJETIVA),
        ('Há regras de governança e qualidade de dados?', TipoPergunta.OBJETIVA),
        ('Descreva onde ficam os principais dados da empresa.', TipoPergunta.DISSERTATIVA),
    ]),
    ('Pessoas', 1, [
        ('A equipe recebeu capacitação em IA?', TipoPergunta.OBJETIVA),
        ('Como a equipe reage à automação de tarefas?', TipoPergunta.DISSERTATIVA),
    ]),
]


class Command(BaseCommand):
    help = 'Cria empresa, usuário "demo" e um questionário publicado para desenvolvimento local.'

    def add_arguments(self, parser):
        parser.add_argument('--senha', required=True, help='Senha do usuário demo.')

    @transaction.atomic
    def handle(self, *args, senha, **options):
        empresa, _ = Empresa.objects.get_or_create(nome='Empresa Exemplo', defaults={'setor': 'Varejo'})
        usuario, _ = Usuario.objects.get_or_create(username='demo', defaults={'empresa': empresa})
        usuario.set_password(senha)
        usuario.save()

        questionario, criado = Questionario.objects.get_or_create(versao=VERSAO_EXEMPLO)
        if criado:
            for ordem, (nome, peso, perguntas) in enumerate(DIMENSOES, start=1):
                dimensao = Dimensao.objects.create(questionario=questionario, nome=nome, peso=peso, ordem=ordem)
                for ordem_pergunta, (texto, tipo) in enumerate(perguntas, start=1):
                    Pergunta.objects.create(dimensao=dimensao, texto=texto, tipo=tipo, peso=1, ordem=ordem_pergunta)
        if not Questionario.objects.filter(ativo=True).exists():
            questionario.publicar()
        self.stdout.write(self.style.SUCCESS('Dados de exemplo prontos. Usuário: demo'))
