from django.apps import AppConfig


class PainelConfig(AppConfig):
    """Aparência do painel administrativo (Django admin) com a identidade visual do produto.

    Só templates e CSS: as funções, permissões e rotas do admin continuam as do Django.
    Fica antes de `django.contrib.admin` em INSTALLED_APPS para os templates daqui terem prioridade.
    """

    name = 'apps.painel'
    verbose_name = 'Painel administrativo'

    def ready(self):
        from django.conf import settings
        from django.contrib import admin

        admin.site.site_header = 'Adoção de IA'
        admin.site.site_title = 'Painel administrativo · Adoção de IA'
        admin.site.index_title = 'Visão geral'
        # "Ver o site" leva ao front-end, não à raiz da API
        admin.site.site_url = settings.FRONTEND_URL
