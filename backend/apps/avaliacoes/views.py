from django.http import Http404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.contas.tenancy import TenantViewMixin
from apps.questionarios.models import Questionario

from . import services
from .models import Avaliacao, StatusAvaliacao
from .serializers import AvaliacaoResumoSerializer, AvaliacaoSerializer, RascunhoSerializer


class AvaliacaoViewSet(TenantViewMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Avaliacao.objects.select_related('questionario')

    def get_serializer_class(self):
        return AvaliacaoResumoSerializer if self.action == 'list' else AvaliacaoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('respostas', 'pontuacoes__dimensao')
        return queryset

    def create(self, request):
        try:
            avaliacao, criada = services.iniciar_avaliacao(request.user.empresa)
        except Questionario.DoesNotExist:
            raise Http404('Nenhuma versão do questionário está publicada.')
        return Response(
            AvaliacaoSerializer(avaliacao).data, status=status.HTTP_201_CREATED if criada else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['patch'])
    def rascunho(self, request, pk=None):
        avaliacao = self.get_object()
        serializer = RascunhoSerializer(data=request.data, context={'avaliacao': avaliacao})
        serializer.is_valid(raise_exception=True)
        services.salvar_rascunho(avaliacao, serializer.validated_data['respostas'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        avaliacao = services.submeter(self.get_object())
        processando = avaliacao.status == StatusAvaliacao.PROCESSANDO_IA
        return Response(
            AvaliacaoSerializer(avaliacao).data,
            status=status.HTTP_202_ACCEPTED if processando else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        avaliacao = self.get_object()
        return Response({'id': str(avaliacao.id), 'status': avaliacao.status})
