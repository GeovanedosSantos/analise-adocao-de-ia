from django.http import Http404, HttpResponse
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.contas.tenancy import TenantViewMixin
from apps.questionarios.models import Questionario

from . import relatorio, services
from .models import Avaliacao, StatusAvaliacao
from .serializers import AvaliacaoHistoricoSerializer, AvaliacaoResumoSerializer, AvaliacaoSerializer, RascunhoSerializer


class AvaliacaoViewSet(TenantViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Avaliacao.objects.select_related('questionario')

    def get_serializer_class(self):
        if self.action == 'historico':
            return AvaliacaoHistoricoSerializer
        return AvaliacaoResumoSerializer if self.action == 'list' else AvaliacaoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ('retrieve', 'pdf'):
            queryset = queryset.select_related('empresa').prefetch_related(
                'respostas__pergunta__dimensao', 'pontuacoes__dimensao__fatores', 'recomendacoes__recomendacao',
            )
        elif self.action == 'historico':
            queryset = queryset.prefetch_related('pontuacoes__dimensao__fatores')
        return queryset

    def list(self, request):
        avaliacoes = services.anexar_deltas_em_lote(list(self.filter_queryset(self.get_queryset())))
        return Response(self.get_serializer(avaliacoes, many=True).data)

    def retrieve(self, request, pk=None):
        avaliacao = services.anexar_deltas(self.get_object())
        return Response(self.get_serializer(avaliacao).data)

    @action(detail=False, methods=['get'])
    def historico(self, request):
        avaliacoes = services.anexar_deltas_em_lote(list(self.filter_queryset(self.get_queryset())), com_dimensoes=True)
        return Response(self.get_serializer(avaliacoes, many=True).data)

    def create(self, request):
        try:
            avaliacao, criada = services.iniciar_avaliacao(request.user.empresa)
        except Questionario.DoesNotExist:
            raise Http404('Nenhuma versão do questionário está publicada.')
        return Response(
            AvaliacaoSerializer(services.anexar_deltas(avaliacao)).data,
            status=status.HTTP_201_CREATED if criada else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['patch'])
    def rascunho(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = RascunhoSerializer(data=request.data, context={'avaliacao': avaliacao})
        serializer.is_valid(raise_exception=True)
        services.salvar_rascunho(avaliacao, serializer.validated_data['respostas'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def descartar(self, request, pk=None):
        """Recomeça o rascunho do zero (UC02 FA02)."""
        services.descartar_rascunho(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        avaliacao = services.submeter(self.get_object())
        processando = avaliacao.status == StatusAvaliacao.PROCESSANDO_IA
        return Response(
            AvaliacaoSerializer(services.anexar_deltas(avaliacao)).data,
            status=status.HTTP_202_ACCEPTED if processando else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        avaliacao = self.get_object()
        return Response({'id': str(avaliacao.id), 'status': avaliacao.status})

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        avaliacao = self.get_object()
        if avaliacao.status == StatusAvaliacao.RASCUNHO:
            return Response({'detail': 'O relatório só existe depois que a avaliação é enviada.'}, status=409)
        conteudo = relatorio.gerar_pdf(services.anexar_deltas(avaliacao))
        resposta = HttpResponse(conteudo, content_type='application/pdf')
        data = (avaliacao.data_fim or avaliacao.data_inicio).strftime('%Y-%m-%d')
        resposta['Content-Disposition'] = f'attachment; filename="avaliacao-prontidao-ia-{data}.pdf"'
        return resposta
