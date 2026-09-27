from django.db import transaction

from .models import AuditoriaAcesso
from .tenancy import ATRIBUTO_AUDITORIA, ignorar_rls


class AuditoriaMiddleware:
    """Grava os acessos bloqueados depois da view, fora da transação que sofreu rollback."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        pendentes = getattr(request, ATRIBUTO_AUDITORIA, None)
        if pendentes:
            AuditoriaAcesso.objects.bulk_create(AuditoriaAcesso(**registro) for registro in pendentes)
        return response


class AdminRlsBypassMiddleware:
    """O painel administrativo gerencia dados de todas as empresas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not (request.path.startswith('/admin/') and request.user.is_authenticated and request.user.is_staff):
            return self.get_response(request)
        with transaction.atomic(), ignorar_rls():
            return self.get_response(request)
