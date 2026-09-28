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

Com o Docker rodando (Postgres e Redis), aplique as migrations e crie os dados de exemplo (empresa, usuário `demo` e um questionário publicado):

``` bash
python manage.py migrate
python manage.py criar_dados_exemplo --senha <escolha-uma-senha>
```

e rode a API:

``` bash
python manage.py runserver
```

Em outro terminal, rode o worker do Celery, que processa as respostas abertas com a IA:

``` bash
celery -A config worker --pool=solo -l info   # --pool=solo é necessário no Windows
```

A análise usa um [Ollama](https://ollama.com/) local (`OLLAMA_URL`, padrão `http://localhost:11434`) com o modelo de `OLLAMA_MODEL`. Sem o Ollama, a avaliação é calculada normalmente e só a análise das respostas abertas termina em "Erro de Processamento".

### Testes

``` bash
cd backend && python manage.py test apps   # precisa do Postgres rodando
cd frontend && npm test
```

### Segurança do banco (RLS)

As tabelas de avaliação têm Row-Level Security por empresa. O Postgres **ignora RLS para superusuários**, e o usuário criado pelo docker-compose é superusuário: em desenvolvimento, o isolamento vem só do filtro da API. Em produção, a aplicação deve conectar com um papel sem `SUPERUSER` e sem `BYPASSRLS`.

