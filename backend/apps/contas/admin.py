from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditoriaAcesso, ContaGoogle, Empresa, Usuario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'setor', 'data_cadastro']
    search_fields = ['nome']


class ContaGoogleInline(admin.StackedInline):
    """Mostra se o usuário entra com Google. O vínculo nasce só pelo fluxo de login, nunca à mão."""

    model = ContaGoogle
    can_delete = True
    extra = 0
    max_num = 1
    readonly_fields = ['email', 'sub', 'criado_em']
    fields = ['email', 'sub', 'criado_em']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'empresa', 'is_staff']
    list_filter = ['empresa', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (('Empresa', {'fields': ['empresa']}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Empresa', {'fields': ['empresa']}),)
    inlines = [ContaGoogleInline]


@admin.register(AuditoriaAcesso)
class AuditoriaAcessoAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'usuario', 'recurso', 'recurso_id', 'empresa_recurso_id', 'ip']
    list_filter = ['recurso']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
