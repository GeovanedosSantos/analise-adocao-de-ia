from rest_framework import serializers

from apps.questionarios.models import Pergunta, TipoPergunta

from .models import ESCALA_MAX, ESCALA_MIN, Avaliacao, PontuacaoDimensao, RecomendacaoAvaliacao, Resposta


class RespostaSerializer(serializers.ModelSerializer):
    pergunta = serializers.UUIDField(source='pergunta_id', read_only=True)

    class Meta:
        model = Resposta
        fields = ['pergunta', 'valor_objetivo', 'texto_aberto', 'feedback_ia']


class PontuacaoDimensaoSerializer(serializers.ModelSerializer):
    dimensao_codigo = serializers.CharField(source='dimensao.codigo')
    dimensao_nome = serializers.CharField(source='dimensao.nome')
    dimensao_peso = serializers.FloatField(source='dimensao.peso')
    fatores = serializers.SerializerMethodField()
    # Deltas (RF12) são derivados na leitura por services.anexar_deltas; None quando não há anterior
    nota_anterior = serializers.SerializerMethodField()
    delta_percentual = serializers.SerializerMethodField()

    class Meta:
        model = PontuacaoDimensao
        fields = ['dimensao', 'dimensao_codigo', 'dimensao_nome', 'dimensao_peso', 'fatores', 'nota', 'prioritaria',
                  'nota_anterior', 'delta_percentual']

    def get_fatores(self, pontuacao):
        return [fator.nome for fator in pontuacao.dimensao.fatores.all()]

    def get_nota_anterior(self, pontuacao):
        return getattr(pontuacao, 'nota_anterior', None)

    def get_delta_percentual(self, pontuacao):
        return getattr(pontuacao, 'delta_percentual', None)


class RecomendacaoAvaliacaoSerializer(serializers.ModelSerializer):
    codigo = serializers.CharField(source='recomendacao.codigo')
    dimensao_codigo = serializers.CharField(source='recomendacao.dimensao_codigo')
    titulo = serializers.CharField(source='recomendacao.titulo')
    descricao = serializers.CharField(source='recomendacao.descricao')
    prazo = serializers.CharField(source='recomendacao.prazo')
    prioridade = serializers.CharField(source='recomendacao.prioridade')
    esforco = serializers.CharField(source='recomendacao.esforco')
    impacto = serializers.CharField(source='recomendacao.impacto')
    kpi = serializers.CharField(source='recomendacao.kpi')

    class Meta:
        model = RecomendacaoAvaliacao
        fields = ['posicao', 'nota_dimensao', 'codigo', 'dimensao_codigo', 'titulo', 'descricao', 'prazo',
                  'prioridade', 'esforco', 'impacto', 'kpi']


class AvaliacaoResumoSerializer(serializers.ModelSerializer):
    versao_questionario = serializers.CharField(source='questionario.versao')
    nota_geral_anterior = serializers.SerializerMethodField()
    delta_nota_geral = serializers.SerializerMethodField()

    class Meta:
        model = Avaliacao
        fields = ['id', 'status', 'versao_questionario', 'data_inicio', 'data_fim', 'nota_geral',
                  'nivel_prontidao', 'nota_geral_anterior', 'delta_nota_geral']

    def get_nota_geral_anterior(self, avaliacao):
        return getattr(avaliacao, 'nota_geral_anterior', None)

    def get_delta_nota_geral(self, avaliacao):
        return getattr(avaliacao, 'delta_nota_geral', None)


class AvaliacaoHistoricoSerializer(AvaliacaoResumoSerializer):
    pontuacoes = PontuacaoDimensaoSerializer(many=True, read_only=True)

    class Meta(AvaliacaoResumoSerializer.Meta):
        fields = AvaliacaoResumoSerializer.Meta.fields + ['pontuacoes']


class AvaliacaoSerializer(AvaliacaoResumoSerializer):
    respostas = RespostaSerializer(many=True)
    pontuacoes = PontuacaoDimensaoSerializer(many=True)
    recomendacoes = RecomendacaoAvaliacaoSerializer(many=True)

    class Meta(AvaliacaoResumoSerializer.Meta):
        fields = AvaliacaoResumoSerializer.Meta.fields + [
            'questionario', 'respostas', 'pontuacoes', 'recomendacoes', 'recomendacoes_ordenadas_ia',
        ]


class ItemRascunhoSerializer(serializers.Serializer):
    pergunta = serializers.PrimaryKeyRelatedField(queryset=Pergunta.objects.select_related('dimensao'))
    valor_objetivo = serializers.IntegerField(min_value=ESCALA_MIN, max_value=ESCALA_MAX, required=False, allow_null=True)
    texto_aberto = serializers.CharField(required=False, allow_blank=True, max_length=5000)

    def validate(self, dados):
        pergunta = dados['pergunta']
        avaliacao = self.context['avaliacao']
        if (
            pergunta.dimensao.questionario_id != avaliacao.questionario_id
            or not pergunta.ativa
            or not pergunta.dimensao.ativa
        ):
            raise serializers.ValidationError({'pergunta': 'A pergunta não faz parte desta avaliação.'})
        if pergunta.tipo == TipoPergunta.OBJETIVA and 'texto_aberto' in dados:
            raise serializers.ValidationError({'texto_aberto': 'Pergunta objetiva aceita apenas valor_objetivo.'})
        if pergunta.tipo == TipoPergunta.DISSERTATIVA and dados.get('valor_objetivo') is not None:
            raise serializers.ValidationError({'valor_objetivo': 'Pergunta dissertativa aceita apenas texto_aberto.'})
        return dados


class RascunhoSerializer(serializers.Serializer):
    respostas = ItemRascunhoSerializer(many=True, allow_empty=False)
