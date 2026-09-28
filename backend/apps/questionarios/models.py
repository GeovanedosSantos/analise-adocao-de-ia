import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Questionario(models.Model):
    """Uma versão do questionário. Só uma versão fica ativa para novas avaliações (US01)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    versao = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateField(auto_now_add=True)
    ativo = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data_criacao', '-versao']
        verbose_name = 'questionário'
        constraints = [
            models.UniqueConstraint(fields=['ativo'], condition=models.Q(ativo=True), name='um_questionario_ativo'),
        ]

    def __str__(self):
        return f'v{self.versao}' + (' (ativa)' if self.ativo else '')

    @property
    def bloqueado(self):
        """Versão já respondida: a estrutura fica congelada para preservar o histórico."""
        # Rascunhos ('DRAFT') ainda não geraram resultado, então não travam a versão
        return self.avaliacoes.exclude(status='DRAFT').exists()

    @transaction.atomic
    def publicar(self):
        """Ativa esta versão e arquiva a anterior."""
        Questionario.objects.filter(ativo=True).exclude(pk=self.pk).update(ativo=False)
        self.ativo = True
        self.save(update_fields=['ativo'])

    @transaction.atomic
    def nova_versao(self, versao):
        """Copia dimensões e perguntas para uma nova versão, ainda não publicada."""
        copia = Questionario.objects.create(versao=versao, descricao=self.descricao)
        for dimensao in self.dimensoes.prefetch_related('perguntas'):
            nova_dimensao = Dimensao.objects.create(
                questionario=copia, nome=dimensao.nome, peso=dimensao.peso, ordem=dimensao.ordem,
            )
            Pergunta.objects.bulk_create(
                Pergunta(dimensao=nova_dimensao, texto=p.texto, tipo=p.tipo, peso=p.peso, ordem=p.ordem, ativa=p.ativa)
                for p in dimensao.perguntas.all()
            )
        return copia


class EstruturaVersionada(models.Model):
    """Impede alterar a estrutura de uma versão já respondida. Inativar e reordenar continuam livres."""

    CAMPOS_LIVRES = {'ativa', 'ordem'}

    class Meta:
        abstract = True

    def get_questionario(self):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if self.get_questionario().bloqueado and self._altera_estrutura():
            raise ValidationError(
                'Esta versão do questionário já foi respondida. Crie uma nova versão para alterá-la.'
            )
        super().save(*args, **kwargs)

    def _altera_estrutura(self):
        original = type(self).objects.filter(pk=self.pk).first() if not self._state.adding else None
        if original is None:
            return True
        campos = [f.attname for f in self._meta.concrete_fields if f.name not in self.CAMPOS_LIVRES]
        return any(getattr(original, c) != getattr(self, c) for c in campos)


class Dimensao(EstruturaVersionada):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE, related_name='dimensoes')
    nome = models.CharField(max_length=255)
    peso = models.FloatField(help_text='Peso da dimensão no índice geral de prontidão.')
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'dimensão'
        verbose_name_plural = 'dimensões'
        constraints = [
            models.CheckConstraint(condition=models.Q(peso__gt=0), name='dimensao_peso_positivo'),
            models.UniqueConstraint(fields=['questionario', 'nome'], name='dimensao_nome_unico_na_versao'),
        ]

    def __str__(self):
        return self.nome

    def get_questionario(self):
        return self.questionario


class TipoPergunta(models.TextChoices):
    OBJETIVA = 'OBJETIVA', 'Objetiva'
    DISSERTATIVA = 'DISSERTATIVA', 'Dissertativa'


class Pergunta(EstruturaVersionada):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dimensao = models.ForeignKey(Dimensao, on_delete=models.CASCADE, related_name='perguntas')
    texto = models.TextField()
    tipo = models.CharField(max_length=20, choices=TipoPergunta.choices)
    peso = models.FloatField(help_text='Peso da pergunta dentro da dimensão.')
    ordem = models.PositiveSmallIntegerField(default=0)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordem']
        constraints = [
            models.CheckConstraint(condition=models.Q(peso__gt=0), name='pergunta_peso_positivo'),
        ]

    def __str__(self):
        return self.texto[:80]

    def get_questionario(self):
        return self.dimensao.questionario
