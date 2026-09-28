from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditoriaAcesso, Empresa, Usuario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'setor', 'data_cadastro']
    search_fields = ['nome']


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'email', 'empresa', 'is_staff']
    list_filter = ['empresa', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (('Empresa', {'fields': ['empresa']}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Empresa', {'fields': ['empresa']}),)


@admin.register(AuditoriaAcesso)
class AuditoriaAcessoAdmin(admin.ModelAdmin):
    list_display = ['criado_em', 'usuario', 'recurso', 'recurso_id', 'empresa_recurso_id', 'ip']
    list_filter = ['recurso']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
