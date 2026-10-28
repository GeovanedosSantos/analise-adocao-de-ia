"""Identificador de correlação entre a API e os workers (seção 5.3).

Cada requisição recebe um id (o do cabeçalho X-Request-ID, se vier, ou um novo). Ele aparece em todas
as linhas de log, volta na resposta e segue junto das tarefas do Celery disparadas pela requisição.
"""

import logging
import re
import uuid
from contextvars import ContextVar

from celery.signals import before_task_publish, task_postrun, task_prerun

CABECALHO = 'X-Request-ID'
_FORMATO_VALIDO = re.compile(r'^[A-Za-z0-9._-]{1,64}$')
_id_atual = ContextVar('id_correlacao', default='-')


def id_atual():
    return _id_atual.get()


class IdCorrelacaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        recebido = request.headers.get(CABECALHO, '')
        # Só aceita o id do cliente se for curto e sem caracteres estranhos, para não poluir os logs
        token = _id_atual.set(recebido if _FORMATO_VALIDO.match(recebido) else uuid.uuid4().hex)
        try:
            response = self.get_response(request)
            response[CABECALHO] = id_atual()
            return response
        finally:
            _id_atual.reset(token)


class IdCorrelacaoFiltro(logging.Filter):
    def filter(self, record):
        record.id_correlacao = id_atual()
        return True


@before_task_publish.connect
def _enviar_com_a_tarefa(headers=None, **kwargs):
    if headers is not None:
        headers['id_correlacao'] = id_atual()


@task_prerun.connect
def _restaurar_no_worker(task=None, **kwargs):
    task._token_correlacao = _id_atual.set(getattr(task.request, 'id_correlacao', None) or uuid.uuid4().hex)


@task_postrun.connect
def _limpar_no_worker(task=None, **kwargs):
    token = getattr(task, '_token_correlacao', None)
    if token is not None:
        _id_atual.reset(token)
        task._token_correlacao = None
