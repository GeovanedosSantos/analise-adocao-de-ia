"""Isolamento entre empresas (RNF01, RNF04, US02).

Duas camadas independentes:
1. Aplicação: toda consulta de uma view de tenant é filtrada pela empresa do usuário autenticado,
   e o acesso direto a um objeto de outra empresa responde 403 e gera registro de auditoria.
2. Banco: políticas de Row-Level Security leem `app.empresa_id`, definido com SET LOCAL na
   transação da requisição. Só valem quando a aplicação conecta com um papel que não é
   superusuário (superusuários ignoram RLS).
"""

import logging
from contextlib import contextmanager

from django.db import connection
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

logger = logging.getLogger('auditoria')

ATRIBUTO_AUDITORIA = '_auditorias_pendentes'


def definir_empresa_rls(empresa_id):
    """Define o tenant da transação atual para as políticas de RLS."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.empresa_id', %s, true)", [str(empresa_id)])


@contextmanager
def ignorar_rls():
    """Libera todas as linhas para workers e admin; exige uma transação aberta."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.ignorar_rls', 'on', true)")
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.ignorar_rls', 'off', true)")


class PertenceAEmpresa(BasePermission):
    message = 'Usuário não está vinculado a nenhuma empresa.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.empresa_id)


class TenantViewMixin:
    """Restringe uma view DRF aos dados da empresa do usuário autenticado.

    A view define `queryset` com o modelo que tem o campo `empresa`.
    """

    permission_classes = [PertenceAEmpresa]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        definir_empresa_rls(request.user.empresa_id)

    def get_queryset(self):
        return super().get_queryset().filter(empresa_id=self.request.user.empresa_id)

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            self._bloquear_se_for_de_outra_empresa()
            raise

    def _bloquear_se_for_de_outra_empresa(self):
        recurso_id = self.kwargs[self.lookup_url_kwarg or self.lookup_field]
        with ignorar_rls():
            alheio = self.queryset.model.objects.filter(**{self.lookup_field: recurso_id}).values('empresa_id').first()
        if alheio is not None:
            registrar_acesso_bloqueado(self.request, self.queryset.model, recurso_id, alheio['empresa_id'])
            raise PermissionDenied('Recurso pertence a outra empresa.')


def registrar_acesso_bloqueado(request, modelo, recurso_id, empresa_recurso_id):
    """Guarda o registro para gravação após a requisição.

    A transação da requisição sofre rollback quando a view responde com erro, então o
    `AuditoriaMiddleware` grava o registro depois dela, fora da transação.
    """
    registro = {
        'usuario_id': request.user.pk,
        'empresa_usuario_id': request.user.empresa_id,
        'recurso': modelo._meta.label,
        'recurso_id': str(recurso_id),
        'empresa_recurso_id': empresa_recurso_id,
        'metodo': request.method,
        'caminho': request.get_full_path()[:500],
        'ip': request.META.get('REMOTE_ADDR'),
    }
    logger.warning(
        'Acesso bloqueado: usuário %(usuario_id)s (empresa %(empresa_usuario_id)s) tentou acessar '
        '%(recurso)s %(recurso_id)s da empresa %(empresa_recurso_id)s',
        registro,
    )
    django_request = getattr(request, '_request', request)
    pendentes = getattr(django_request, ATRIBUTO_AUDITORIA, None)
    if pendentes is None:
        pendentes = []
        setattr(django_request, ATRIBUTO_AUDITORIA, pendentes)
    pendentes.append(registro)
