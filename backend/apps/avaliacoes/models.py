import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.contas.models import Empresa
from apps.questionarios.models import Dimensao, Pergunta, Questionario
from apps.recomendacoes.models import Recomendacao

ESCALA_MIN, ESCALA_MAX = 1, 5  # escala Likert das perguntas objetivas


class StatusAvaliacao(models.TextChoices):
    RASCUNHO = 'DRAFT', 'Rascunho'
    PROCESSANDO_IA = 'PROCESSANDO_IA', 'Processando IA'
    ERRO_PROCESSAMENTO = 'ERRO_PROCESSAMENTO', 'Erro de processamento'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'


class Avaliacao(models.Model):
    """Uma rodada de avaliação de uma empresa, presa à versão do questionário em que foi respondida."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='avaliacoes')
    questionario = models.ForeignKey(Questionario, on_delete=models.PROTECT, related_name='avaliacoes')
    status = models.CharField(max_length=20, choices=StatusAvaliacao.choices, default=StatusAvaliacao.RASCUNHO)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    nota_geral = models.FloatField(null=True, blank=True)
    nivel_prontidao = models.PositiveSmallIntegerField(null=True, blank=True, help_text='De 1 a 5.')
    recomendacoes_ordenadas_ia = models.BooleanField(
        default=False, help_text='O plano de ação já foi ranqueado pela IA; senão, segue a ordem das faixas.',
    )
    versao_prompts_ia = models.CharField(
        max_length=20, blank=True, help_text='Versão dos prompts da IA que ranqueou o plano de ação.',
    )

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'avaliação'
        verbose_name_plural = 'avaliações'
        constraints = [
            models.UniqueConstraint(
                fields=['empresa'], condition=models.Q(status='DRAFT'), name='um_rascunho_por_empresa',
            ),
        ]

    def __str__(self):
        return f'{self.empresa} · {self.data_inicio:%d/%m/%Y} · {self.get_status_display()}'


class PontuacaoDimensao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='pontuacoes')
    dimensao = models.ForeignKey(Dimensao, on_delete=models.PROTECT, related_name='+')
    nota = models.FloatField(help_text='De 0 a 100.')
    prioritaria = models.BooleanField(default=False)

    class Meta:
        ordering = ['dimensao__ordem']
        verbose_name = 'pontuação por dimensão'
        verbose_name_plural = 'pontuações por dimensão'
        constraints = [
            models.UniqueConstraint(fields=['avaliacao', 'dimensao'], name='uma_pontuacao_por_dimensao'),
        ]


class Resposta(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='respostas')
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name='+')
    valor_objetivo = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(ESCALA_MIN), MaxValueValidator(ESCALA_MAX)],
    )
    texto_aberto = models.TextField(blank=True)
    feedback_ia = models.JSONField(null=True, blank=True)
    tentativas_ia = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['avaliacao', 'pergunta'], name='uma_resposta_por_pergunta'),
            models.CheckConstraint(
                condition=models.Q(valor_objetivo__isnull=True)
                | models.Q(valor_objetivo__gte=ESCALA_MIN, valor_objetivo__lte=ESCALA_MAX),
                name='valor_objetivo_na_escala',
            ),
        ]


class RecomendacaoAvaliacao(models.Model):
    """Uma das recomendações do catálogo escolhidas para o plano de ação da avaliação (RF10)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='recomendacoes')
    recomendacao = models.ForeignKey(Recomendacao, on_delete=models.PROTECT, related_name='+')
    posicao = models.PositiveSmallIntegerField(help_text='1 é a mais importante.')
    nota_dimensao = models.FloatField(help_text='Nota da dimensão que fez a recomendação ser escolhida.')

    class Meta:
        ordering = ['posicao']
        verbose_name = 'recomendação da avaliação'
        verbose_name_plural = 'recomendações da avaliação'
        constraints = [
            models.UniqueConstraint(fields=['avaliacao', 'recomendacao'], name='recomendacao_unica_na_avaliacao'),
            models.UniqueConstraint(
                fields=['avaliacao', 'posicao'], name='posicao_unica_na_avaliacao', deferrable=models.Deferrable.DEFERRED,
            ),
        ]
