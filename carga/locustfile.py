"""Teste de carga (Sprint 4, RNF05, RNF06 e RNF10).

Cada usuário virtual entra, lê o questionário, o histórico e o catálogo, responde e envia uma avaliação,
e acompanha o status até a IA terminar. Mede as rotas síncronas e a fila do Celery ao mesmo tempo.

Pré-requisitos: API, Redis, PostgreSQL, worker do Celery e Ollama no ar, e usuários de carga criados
(carga-1 ... carga-N, todos com a mesma senha, cada um na própria empresa). Uso:

    pip install locust
    CARGA_SENHA=... locust -f carga/locustfile.py --host http://localhost:8000 -u 20 -r 2 -t 5m
"""

import itertools
import os
import random
import time

from locust import HttpUser, between, task

SENHA = os.environ.get('CARGA_SENHA', '')
_numeros = itertools.count(1)


class Empresa(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        usuario = f'carga-{next(_numeros)}'
        token = self.client.post('/api/v1/auth/token/', json={'username': usuario, 'password': SENHA}).json()
        self.client.headers['Authorization'] = f'Bearer {token["access"]}'

    @task(5)
    def navegar(self):
        self.client.get('/api/v1/avaliacoes/historico/')
        self.client.get('/api/v1/recomendacoes/')

    @task(1)
    def responder_e_enviar(self):
        questionario = self.client.get('/api/v1/questionarios/ativo/').json()
        avaliacao = self.client.post('/api/v1/avaliacoes/').json()
        respostas = []
        for dimensao in questionario['dimensoes']:
            for pergunta in dimensao['perguntas']:
                if pergunta['tipo'] == 'OBJETIVA':
                    respostas.append({'pergunta': pergunta['id'], 'valor_objetivo': random.randint(1, 5)})
                else:
                    respostas.append({'pergunta': pergunta['id'], 'texto_aberto': 'Usamos planilhas e um ERP antigo.'})
        self.client.patch(f'/api/v1/avaliacoes/{avaliacao["id"]}/rascunho/', json={'respostas': respostas},
                          name='/api/v1/avaliacoes/[id]/rascunho/')
        self.client.post(f'/api/v1/avaliacoes/{avaliacao["id"]}/submeter/', name='/api/v1/avaliacoes/[id]/submeter/')
        for _ in range(60):  # acompanha a fila por até 2 minutos
            status = self.client.get(f'/api/v1/avaliacoes/{avaliacao["id"]}/status/',
                                     name='/api/v1/avaliacoes/[id]/status/').json()['status']
            if status != 'PROCESSANDO_IA':
                break
            time.sleep(2)
