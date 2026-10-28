from rest_framework import serializers

from .models import Dimensao, Pergunta, Questionario


class PerguntaSerializer(serializers.ModelSerializer):
    fator = serializers.CharField(source='fator.nome', default=None)

    class Meta:
        model = Pergunta
        fields = ['id', 'texto', 'tipo', 'ordem', 'fator']


class DimensaoSerializer(serializers.ModelSerializer):
    perguntas = PerguntaSerializer(many=True, source='perguntas_ativas')

    class Meta:
        model = Dimensao
        fields = ['id', 'codigo', 'nome', 'descricao', 'ordem', 'perguntas']


class QuestionarioSerializer(serializers.ModelSerializer):
    dimensoes = DimensaoSerializer(many=True, source='dimensoes_ativas')

    class Meta:
        model = Questionario
        fields = ['id', 'versao', 'descricao', 'dimensoes']
