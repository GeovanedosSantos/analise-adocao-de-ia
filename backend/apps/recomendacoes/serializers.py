from rest_framework import serializers

from .models import Recomendacao


class RecomendacaoSerializer(serializers.ModelSerializer):
    dimensao_nome = serializers.SerializerMethodField()

    class Meta:
        model = Recomendacao
        fields = ['id', 'codigo', 'dimensao_codigo', 'dimensao_nome', 'titulo', 'descricao', 'nota_minima',
                  'nota_maxima', 'prazo', 'prioridade', 'esforco', 'impacto', 'kpi']

    def get_dimensao_nome(self, recomendacao):
        """Nome da dimensão na versão ativa do questionário; o código, se ela não existir lá."""
        return self.context.get('nomes_dimensoes', {}).get(recomendacao.dimensao_codigo, recomendacao.dimensao_codigo)
