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

e rode:

``` bash
python manage.py runserver
```

