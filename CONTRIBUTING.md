### Docker

Copie o arquivo .env-example como .env e preencha as variáveis de ambiente:

>POSTGRES_DB=nomedb\
>POSTGRES_USER=userdb\
>POSTGRES_PASSWORD=senhadb

**É importante que o arquivo com as variáveis preenchidas seja chamado .env**

 depois rode o comando:

``` bash
docker-compose up -d
```

### Frontend

Instale a versão do node no que está no arquivo .nvmrc localmente na sua maquina, ou usando uma ferramenta como [nvm](https://www.nvmnode.com/pt) ou [mise](https://mise.jdx.dev/).

Instale as dependências (apenas na primeira vez que clonar o repositório): 

``` bash
npm install
```

e rode:

``` bash
npm run dev
```

### Backend

Instale a versão do python do arquivo .python-version e crie o ambiente virtual:

``` bash
python -m venv .venv
.\.venv\Scripts\activate # Windows
source .venv/bin/activate # Linux/macOS
```

instale as dependencias:

``` bash
pip install -r requirements.txt
```

Com o Docker rodando (Postgres e Redis), aplique as migrations e crie os dados de exemplo (empresa, usuário `demo`, o modelo de prontidão com 5 dimensões, 19 fatores e 38 itens, e o catálogo inicial de recomendações):

``` bash
python manage.py migrate
python manage.py criar_dados_exemplo --senha <escolha-uma-senha>
```

e rode a API:

``` bash
python manage.py runserver
```

O modelo de prontidão sozinho pode ser carregado com `python manage.py carregar_modelo_prontidao` (ele só publica a versão se nenhuma estiver ativa). O catálogo de recomendações é mantido pelo Django admin (`/admin/`).

Em outro terminal, rode o worker do Celery, que analisa as respostas abertas e ranqueia o plano de ação com a IA:

``` bash
celery -A config worker --pool=solo -l info   # --pool=solo é necessário no Windows
```

A análise usa um [Ollama](https://ollama.com/) local (`OLLAMA_URL`, padrão `http://localhost:11434`) com o modelo de `OLLAMA_MODEL`. Sem o Ollama, as notas e o plano de ação pelas faixas de pontuação ficam prontos na hora, e a avaliação termina em "Erro de Processamento".

O relatório em PDF usa o WeasyPrint, que precisa do Pango instalado no sistema (`apt-get install libpango-1.0-0 libpangoft2-1.0-0` no Debian/Ubuntu; no Windows, veja a [documentação do WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)).

O contrato da API fica em `/api/v1/schema/` (OpenAPI) e `/api/v1/schema/docs/` (Swagger).

### Testes

``` bash
cd backend && python manage.py test apps   # precisa do Postgres rodando
cd frontend && npm test
```

Desempenho das rotas síncronas (RNF05, p95 < 500 ms) e do PDF (RNF09, < 5 s), com os dados do usuário `demo`:

``` bash
python manage.py medir_desempenho            # --sem-pdf se o Pango não estiver instalado
```

O teste de carga com workers e IA fica em [carga/locustfile.py](carga/locustfile.py). O CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) roda testes, lint, build, medição de desempenho e auditoria de dependências.

### Segurança do banco (RLS)

As tabelas de avaliação têm Row-Level Security por empresa. O Postgres **ignora RLS para superusuários**, e o usuário criado pelo docker-compose é superusuário: em desenvolvimento, o isolamento vem só do filtro da API. Em produção, a aplicação deve conectar com um papel sem `SUPERUSER` e sem `BYPASSRLS`.

