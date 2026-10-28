from rest_framework.generics import ListAPIView

from apps.questionarios.models import Dimensao

from .models import Recomendacao
from .serializers import RecomendacaoSerializer


class CatalogoView(ListAPIView):
    """Recomendações ativas do catálogo (UC06). O cadastro é feito no Django admin.

    Só entram as recomendações das dimensões da versão publicada do questionário: as de dimensões que
    saíram do modelo nunca seriam sugeridas. A ordem segue a das dimensões no questionário.
    """

    serializer_class = RecomendacaoSerializer
    pagination_class = None

    def get_queryset(self):
        self._dimensoes = list(
            Dimensao.objects.filter(questionario__ativo=True, ativa=True).values_list('codigo', 'nome')
        )
        ordem = {codigo: i for i, (codigo, _) in enumerate(self._dimensoes)}
        recomendacoes = Recomendacao.objects.filter(ativa=True, dimensao_codigo__in=ordem)
        return sorted(recomendacoes, key=lambda r: (ordem[r.dimensao_codigo], r.nota_minima, r.codigo))

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'nomes_dimensoes': dict(getattr(self, '_dimensoes', []))}
