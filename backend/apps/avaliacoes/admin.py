from django.contrib import admin

from .models import Avaliacao, PontuacaoDimensao, Resposta


class PontuacaoInline(admin.TabularInline):
    model = PontuacaoDimensao
    extra = 0
    can_delete = False
    readonly_fields = ['dimensao', 'nota', 'prioritaria', 'delta_percentual']


class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    can_delete = False
    readonly_fields = ['pergunta', 'valor_objetivo', 'texto_aberto', 'feedback_ia', 'tentativas_ia']


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'questionario', 'status', 'nota_geral', 'apta', 'data_inicio']
    list_filter = ['status', 'empresa', 'questionario']
    readonly_fields = ['empresa', 'questionario', 'status', 'data_inicio', 'data_fim', 'nota_geral',
                       'nivel_maturidade', 'apta']
    inlines = [PontuacaoInline, RespostaInline]
