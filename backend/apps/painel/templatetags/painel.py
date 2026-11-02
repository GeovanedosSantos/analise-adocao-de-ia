import hashlib
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@lru_cache
def _versao(caminho):
    arquivo = finders.find(caminho)
    if not arquivo:
        return ''
    with open(arquivo, 'rb') as conteudo:
        return hashlib.sha256(conteudo.read()).hexdigest()[:10]


@register.simple_tag
def static_versionado(caminho):
    """URL do arquivo estático com ?v=<hash do conteúdo>.

    A URL muda sempre que o arquivo muda, então o navegador baixa a versão nova depois de um deploy
    em vez de continuar usando a cópia em cache.
    """
    versao = _versao(caminho)
    return f'{static(caminho)}?v={versao}' if versao else static(caminho)
