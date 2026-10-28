from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView

from .models import Dimensao, Pergunta, Questionario
from .serializers import QuestionarioSerializer


def questionarios_com_estrutura():
    dimensoes_ativas = Prefetch('dimensoes', queryset=Dimensao.objects.filter(ativa=True), to_attr='dimensoes_ativas')
    perguntas_ativas = Prefetch(
        'dimensoes_ativas__perguntas', queryset=Pergunta.objects.filter(ativa=True).select_related('fator'),
        to_attr='perguntas_ativas',
    )
    return Questionario.objects.prefetch_related(dimensoes_ativas, perguntas_ativas)


class QuestionarioView(RetrieveAPIView):
    """Estrutura de uma versão, agrupada por dimensão. Usada para retomar rascunhos (US03)."""

    serializer_class = QuestionarioSerializer
    queryset = questionarios_com_estrutura()


class QuestionarioAtivoView(RetrieveAPIView):
    """Estrutura da versão ativa, agrupada por dimensão (RF01)."""

    serializer_class = QuestionarioSerializer

    def get_object(self):
        return get_object_or_404(questionarios_com_estrutura(), ativo=True)
