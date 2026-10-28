import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.questionarios.models import Dimensao

NOTA_MIN, NOTA_MAX = 0, 100


class Prazo(models.TextChoices):
    CURTO = 'CURTO', 'Curto prazo (0 a 3 meses)'
    MEDIO = 'MEDIO', 'Médio prazo (3 a 6 meses)'
    LONGO = 'LONGO', 'Longo prazo (6 a 12 meses ou mais)'


class Nivel(models.TextChoices):
    """Escala usada para prioridade, esforço e impacto. A ordem dos valores é a da relevância."""

    ALTO = 'ALTO', 'Alto'
    MEDIO = 'MEDIO', 'Médio'
    BAIXO = 'BAIXO', 'Baixo'


class Recomendacao(models.Model):
    """Ação curada por especialistas, aplicável a uma dimensão quando a nota cai na faixa (RF10, UC06).

    A faixa é fechada embaixo e aberta em cima ([nota_minima, nota_maxima)); nota_maxima = 100 inclui o 100.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.SlugField(max_length=50, unique=True, help_text='Identificador estável (ex.: "dados-governanca").')
    dimensao_codigo = models.SlugField(
        max_length=50, help_text='Código da dimensão do questionário (ex.: "dados"). É estável entre versões.',
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(help_text='A ação recomendada, como será exibida para a empresa.')
    nota_minima = models.FloatField(validators=[MinValueValidator(NOTA_MIN), MaxValueValidator(NOTA_MAX)])
    nota_maxima = models.FloatField(validators=[MinValueValidator(NOTA_MIN), MaxValueValidator(NOTA_MAX)])
    prazo = models.CharField(max_length=10, choices=Prazo.choices)
    prioridade = models.CharField(max_length=10, choices=Nivel.choices)
    esforco = models.CharField(max_length=10, choices=Nivel.choices)
    impacto = models.CharField(max_length=10, choices=Nivel.choices)
    kpi = models.CharField('KPI', max_length=255, blank=True, help_text='Métrica que indica o sucesso da ação.')
    ativa = models.BooleanField(default=True, help_text='Inativas deixam de ser sugeridas em novas avaliações.')

    class Meta:
        ordering = ['dimensao_codigo', 'nota_minima', 'codigo']
        verbose_name = 'recomendação'
        verbose_name_plural = 'recomendações'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nota_minima__gte=NOTA_MIN, nota_maxima__lte=NOTA_MAX)
                & models.Q(nota_minima__lt=models.F('nota_maxima')),
                name='faixa_de_nota_valida',
            ),
        ]

    def __str__(self):
        return f'{self.titulo} ({self.dimensao_codigo}, {self.nota_minima:g} a {self.nota_maxima:g})'

    def clean(self):
        erros = {}
        if self.nota_minima is not None and self.nota_maxima is not None and self.nota_minima >= self.nota_maxima:
            erros['nota_maxima'] = 'A nota máxima precisa ser maior que a mínima.'
        # UC11: a recomendação precisa apontar para uma dimensão cadastrada em alguma versão do questionário
        if self.dimensao_codigo and not Dimensao.objects.filter(codigo=self.dimensao_codigo).exists():
            erros['dimensao_codigo'] = 'Não existe dimensão com esse código em nenhuma versão do questionário.'
        if erros:
            raise ValidationError(erros)

    def aplica_a(self, nota):
        return self.nota_minima <= nota < self.nota_maxima or nota == self.nota_maxima == NOTA_MAX
