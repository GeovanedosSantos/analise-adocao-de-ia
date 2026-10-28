import statistics
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from apps.avaliacoes.models import Avaliacao, StatusAvaliacao
from apps.contas.models import Usuario
from apps.contas.tenancy import ignorar_rls

LIMITE_ROTAS_MS = 500  # RNF05
LIMITE_PDF_MS = 5000  # RNF09


class Command(BaseCommand):
    help = (
        'Mede o tempo de resposta das rotas síncronas (RNF05: p95 < 500 ms) e do PDF (RNF09: < 5 s) '
        'com os dados de um usuário existente. Termina com erro se algum limite for ultrapassado.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--usuario', default='demo')
        parser.add_argument('--repeticoes', type=int, default=30)
        parser.add_argument('--sem-pdf', action='store_true', help='Pula o PDF (ex.: sem Pango instalado).')

    def handle(self, *args, usuario, repeticoes, sem_pdf, **options):
        try:
            conta = Usuario.objects.get(username=usuario)
        except Usuario.DoesNotExist:
            raise CommandError(f'Usuário "{usuario}" não existe. Rode criar_dados_exemplo antes.')
        cliente = APIClient(SERVER_NAME=settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost')
        cliente.force_authenticate(conta)
        with ignorar_rls():
            enviada = Avaliacao.objects.filter(empresa=conta.empresa).exclude(status=StatusAvaliacao.RASCUNHO).first()

        rotas = ['/api/v1/questionarios/ativo/', '/api/v1/avaliacoes/', '/api/v1/avaliacoes/historico/',
                 '/api/v1/recomendacoes/']
        if enviada:
            rotas += [f'/api/v1/avaliacoes/{enviada.id}/', f'/api/v1/avaliacoes/{enviada.id}/status/']
        falhas = [rota for rota in rotas if not self._medir(cliente, rota, repeticoes, LIMITE_ROTAS_MS)]
        if enviada and not sem_pdf:
            if not self._medir(cliente, f'/api/v1/avaliacoes/{enviada.id}/pdf/', 3, LIMITE_PDF_MS):
                falhas.append('pdf')
        if falhas:
            raise CommandError(f'Acima do limite: {", ".join(falhas)}')
        self.stdout.write(self.style.SUCCESS('Todas as rotas dentro do limite.'))

    def _medir(self, cliente, rota, repeticoes, limite_ms):
        tempos = []
        for _ in range(repeticoes):
            inicio = time.perf_counter()
            resposta = cliente.get(rota)
            tempos.append((time.perf_counter() - inicio) * 1000)
            if resposta.status_code != 200:
                raise CommandError(f'{rota} respondeu {resposta.status_code}')
        p95 = statistics.quantiles(tempos, n=20)[-1] if len(tempos) > 1 else tempos[0]
        dentro = p95 < limite_ms
        self.stdout.write(
            f'{"ok " if dentro else "LENTO"} {rota}: p50 {statistics.median(tempos):.0f} ms, p95 {p95:.0f} ms '
            f'(limite {limite_ms} ms)'
        )
        return dentro
