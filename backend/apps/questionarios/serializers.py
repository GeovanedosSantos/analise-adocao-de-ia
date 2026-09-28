from rest_framework import serializers

from .models import Dimensao, Pergunta, Questionario


class PerguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = ['id', 'texto', 'tipo', 'ordem']


class DimensaoSerializer(serializers.ModelSerializer):
    perguntas = PerguntaSerializer(many=True, source='perguntas_ativas')

    class Meta:
        model = Dimensao
        fields = ['id', 'nome', 'ordem', 'perguntas']


class QuestionarioSerializer(serializers.ModelSerializer):
    dimensoes = DimensaoSerializer(many=True)

    class Meta:
        model = Questionario
        fields = ['id', 'versao', 'descricao', 'dimensoes']
