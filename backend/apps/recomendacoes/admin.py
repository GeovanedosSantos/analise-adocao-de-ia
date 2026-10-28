from django.contrib import admin

from .models import Recomendacao


@admin.register(Recomendacao)
class RecomendacaoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'dimensao_codigo', 'nota_minima', 'nota_maxima', 'prioridade', 'prazo', 'ativa']
    list_filter = ['dimensao_codigo', 'prioridade', 'prazo', 'ativa']
    list_editable = ['ativa']
    search_fields = ['codigo', 'titulo', 'descricao']
    fieldsets = [
        (None, {'fields': ['codigo', 'dimensao_codigo', 'titulo', 'descricao', 'kpi', 'ativa']}),
        ('Faixa de pontuação da dimensão', {
            'fields': [('nota_minima', 'nota_maxima')],
            'description': 'Sugerida quando a nota fica entre a mínima (inclusive) e a máxima (exclusive); '
                           'máxima 100 inclui a nota 100.',
        }),
        ('Classificação', {'fields': ['prazo', 'prioridade', 'esforco', 'impacto']}),
    ]
