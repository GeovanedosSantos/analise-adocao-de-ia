from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.avaliacoes.views import AvaliacaoViewSet
from apps.contas.views import EntrarView, EsqueciSenhaView, RedefinirSenhaView
from apps.questionarios.views import QuestionarioAtivoView, QuestionarioView
from apps.recomendacoes.views import CatalogoView

router = DefaultRouter()
router.register('avaliacoes', AvaliacaoViewSet, basename='avaliacao')

api_v1 = [
    path('auth/token/', EntrarView.as_view(), name='token'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/senha/esqueci/', EsqueciSenhaView.as_view(), name='senha-esqueci'),
    path('auth/senha/redefinir/', RedefinirSenhaView.as_view(), name='senha-redefinir'),
    # Contrato da API em OpenAPI (seção 5.3)
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-docs'),
    path('questionarios/ativo/', QuestionarioAtivoView.as_view(), name='questionario-ativo'),
    path('questionarios/<uuid:pk>/', QuestionarioView.as_view(), name='questionario'),
    path('recomendacoes/', CatalogoView.as_view(), name='catalogo'),
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1)),
]
