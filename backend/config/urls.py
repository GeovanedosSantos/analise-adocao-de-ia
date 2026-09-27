from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.avaliacoes.views import AvaliacaoViewSet
from apps.questionarios.views import QuestionarioAtivoView, QuestionarioView

router = DefaultRouter()
router.register('avaliacoes', AvaliacaoViewSet, basename='avaliacao')

api_v1 = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('questionarios/ativo/', QuestionarioAtivoView.as_view(), name='questionario-ativo'),
    path('questionarios/<uuid:pk>/', QuestionarioView.as_view(), name='questionario'),
    path('', include(router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1)),
]
