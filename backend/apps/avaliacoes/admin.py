from django.contrib import admin

from .models import Avaliacao, PontuacaoDimensao, RecomendacaoAvaliacao, Resposta


class PontuacaoInline(admin.TabularInline):
    model = PontuacaoDimensao
    extra = 0
    can_delete = False
    readonly_fields = ['dimensao', 'nota', 'prioritaria']


class RecomendacaoInline(admin.TabularInline):
    model = RecomendacaoAvaliacao
    extra = 0
    can_delete = False
    readonly_fields = ['posicao', 'recomendacao', 'nota_dimensao']


class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    can_delete = False
    readonly_fields = ['pergunta', 'valor_objetivo', 'texto_aberto', 'feedback_ia', 'tentativas_ia']


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'questionario', 'status', 'nota_geral', 'nivel_prontidao', 'data_inicio']
    list_filter = ['status', 'empresa', 'questionario']
    readonly_fields = ['empresa', 'questionario', 'status', 'data_inicio', 'data_fim', 'nota_geral',
                       'nivel_prontidao', 'recomendacoes_ordenadas_ia']
    inlines = [PontuacaoInline, RecomendacaoInline, RespostaInline]
