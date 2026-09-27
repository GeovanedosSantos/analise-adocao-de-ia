import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Empresa(models.Model):
    """Entidade raiz do domínio e unidade de isolamento (tenant)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    setor = models.CharField(max_length=100)
    data_cadastro = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    """Funcionário de uma empresa. Sem empresa, só acessa o painel administrativo."""

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True, related_name='usuarios')


class AuditoriaAcesso(models.Model):
    """Tentativa bloqueada de acessar recurso de outra empresa (RNF04)."""

    criado_em = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='+')
    empresa_usuario_id = models.UUIDField(null=True)
    recurso = models.CharField(max_length=100)
    recurso_id = models.CharField(max_length=64)
    empresa_recurso_id = models.UUIDField(null=True)
    metodo = models.CharField(max_length=10)
    caminho = models.CharField(max_length=500)
    ip = models.GenericIPAddressField(null=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'auditoria de acesso'
        verbose_name_plural = 'auditoria de acessos'

    def __str__(self):
        return f'{self.criado_em:%d/%m/%Y %H:%M} {self.recurso} {self.recurso_id}'
