from rest_framework import serializers

from apps.questionarios.models import Pergunta, TipoPergunta

from .models import ESCALA_MAX, ESCALA_MIN, Avaliacao, PontuacaoDimensao, Resposta


class RespostaSerializer(serializers.ModelSerializer):
    pergunta = serializers.UUIDField(source='pergunta_id', read_only=True)

    class Meta:
        model = Resposta
        fields = ['pergunta', 'valor_objetivo', 'texto_aberto', 'feedback_ia']


class PontuacaoDimensaoSerializer(serializers.ModelSerializer):
    dimensao_nome = serializers.CharField(source='dimensao.nome')

    class Meta:
        model = PontuacaoDimensao
        fields = ['dimensao', 'dimensao_nome', 'nota', 'prioritaria']


class AvaliacaoResumoSerializer(serializers.ModelSerializer):
    versao_questionario = serializers.CharField(source='questionario.versao')

    class Meta:
        model = Avaliacao
        fields = ['id', 'status', 'versao_questionario', 'data_inicio', 'data_fim', 'nota_geral',
                  'nivel_maturidade', 'apta']


class AvaliacaoSerializer(AvaliacaoResumoSerializer):
    respostas = RespostaSerializer(many=True)
    pontuacoes = PontuacaoDimensaoSerializer(many=True)

    class Meta(AvaliacaoResumoSerializer.Meta):
        fields = AvaliacaoResumoSerializer.Meta.fields + ['questionario', 'respostas', 'pontuacoes']


class ItemRascunhoSerializer(serializers.Serializer):
    pergunta = serializers.PrimaryKeyRelatedField(queryset=Pergunta.objects.select_related('dimensao'))
    valor_objetivo = serializers.IntegerField(min_value=ESCALA_MIN, max_value=ESCALA_MAX, required=False, allow_null=True)
    texto_aberto = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    def validate(self, dados):
        pergunta = dados['pergunta']
        avaliacao = self.context['avaliacao']
        if pergunta.dimensao.questionario_id != avaliacao.questionario_id or not pergunta.ativa:
            raise serializers.ValidationError({'pergunta': 'A pergunta não faz parte desta avaliação.'})
        if pergunta.tipo == TipoPergunta.OBJETIVA and 'texto_aberto' in dados:
            raise serializers.ValidationError({'texto_aberto': 'Pergunta objetiva aceita apenas valor_objetivo.'})
        if pergunta.tipo == TipoPergunta.DISSERTATIVA and dados.get('valor_objetivo') is not None:
            raise serializers.ValidationError({'valor_objetivo': 'Pergunta dissertativa aceita apenas texto_aberto.'})
        return dados


class RascunhoSerializer(serializers.Serializer):
    respostas = ItemRascunhoSerializer(many=True, allow_empty=False)
