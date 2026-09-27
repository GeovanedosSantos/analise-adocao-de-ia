from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView

from .models import Pergunta, Questionario
from .serializers import QuestionarioSerializer


def questionarios_com_estrutura():
    perguntas_ativas = Prefetch(
        'dimensoes__perguntas', queryset=Pergunta.objects.filter(ativa=True), to_attr='perguntas_ativas',
    )
    return Questionario.objects.prefetch_related(perguntas_ativas)


class QuestionarioView(RetrieveAPIView):
    """Estrutura de uma versão, agrupada por dimensão. Usada para retomar rascunhos (US03)."""

    serializer_class = QuestionarioSerializer
    queryset = questionarios_com_estrutura()


class QuestionarioAtivoView(RetrieveAPIView):
    """Estrutura da versão ativa, agrupada por dimensão (RF01)."""

    serializer_class = QuestionarioSerializer

    def get_object(self):
        return get_object_or_404(questionarios_com_estrutura(), ativo=True)
