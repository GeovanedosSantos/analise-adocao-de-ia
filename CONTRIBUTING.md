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

### Rotas públicas e contas

| Rota (front-end) | O que é |
| --- | --- |
| `/` | Apresentação do produto, com "Entrar" e "Criar conta" no topo. Quem já entrou vê "Ir para o painel". |
| `/login` | Entrada com usuário **ou** e-mail e senha, ou com Google. |
| `/cadastro` | Cria uma empresa e o primeiro usuário dela, e já inicia a sessão. |
| `/entrar/google/retorno` | Volta do Google: entra, pede os dados da empresa (conta nova) ou explica o erro. |

Contas criadas pelo cadastro ou pelo Google **nunca** têm acesso ao painel administrativo (`is_staff` e `is_superuser` ficam falsos). Quem administra o sistema continua sendo criado com `createsuperuser` ou pelo próprio painel.

API usada por essas telas: `POST /api/v1/auth/cadastro/`, `GET /api/v1/auth/google/config/`, `POST /api/v1/auth/google/` e `POST /api/v1/auth/google/concluir/`.

### Entrar com Google

O fluxo é o de autorização com PKCE (OpenID Connect): o front-end leva a pessoa ao Google, o Google devolve um código em `/entrar/google/retorno`, e o Django troca esse código usando o segredo do cliente, que nunca sai do servidor.

1. No [Google Cloud Console](https://console.cloud.google.com/), em **APIs e serviços → Tela de permissão OAuth**, configure o app (tipo externo) com os escopos `openid`, `email` e `profile`.
2. Em **Credenciais → Criar credenciais → ID do cliente OAuth**, escolha **Aplicativo da Web**.
3. Em **URIs de redirecionamento autorizados**, cadastre exatamente o endereço do retorno de cada ambiente:
   - desenvolvimento: `http://localhost:5173/entrar/google/retorno`
   - produção: `https://<seu-dominio>/entrar/google/retorno`
4. Em **Origens JavaScript autorizadas**, cadastre a origem do front-end (`http://localhost:5173`, `https://<seu-dominio>`).
5. Preencha no `.env` do servidor:
   ```
   GOOGLE_CLIENT_ID=<id do cliente>
   GOOGLE_CLIENT_SECRET=<segredo do cliente>
   # Opcional: o padrão é FRONTEND_URL + /entrar/google/retorno
   GOOGLE_REDIRECT_URI=https://<seu-dominio>/entrar/google/retorno
   ```
   O `GOOGLE_REDIRECT_URI` precisa ser idêntico ao cadastrado no Google, e o `FRONTEND_URL` deve apontar para o endereço público do site.
6. Reinicie a API. O botão "Continuar com o Google" passa a funcionar no login e no cadastro.

Enquanto a tela de permissão estiver em modo de **teste**, só os e-mails adicionados como usuários de teste conseguem entrar.

Regras de vínculo:
- A conta Google fica ligada ao usuário pelo identificador do Google (`sub`), não pelo e-mail.
- Se o e-mail do Google já pertence a uma conta criada com senha, a entrada é recusada com uma orientação para entrar com e-mail e senha. Não há vínculo automático, porque o cadastro não confirma o e-mail e alguém poderia criar uma conta com o e-mail de outra pessoa.
- Só são aceitos e-mails confirmados pelo Google.

### Painel administrativo

O `/admin/` continua sendo o Django admin, com as mesmas funções, permissões e rotas. A aparência vem da app `apps/painel` (templates e `static/painel/painel.css`), que fica antes de `django.contrib.admin` em `INSTALLED_APPS` e reaproveita a paleta do front-end, inclusive no tema escuro. Em produção, rode `collectstatic` (ou o mecanismo que já serve o CSS do admin) para publicar o `painel.css`.

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

