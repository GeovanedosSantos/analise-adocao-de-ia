# Code review: Sprints 1 e 2 (código gerado pelo Gemini)

Revisão do código proposto pelo Gemini para as Sprints 1 e 2 do documento do TCC (seção 3.2), comparado com os requisitos (RF01–RF10, RNF01–RNF11) e as histórias US01–US04, e implementação da versão corrigida nesta branch.

**Fontes revisadas:** três exportações da conversa com o Gemini (`Código da Sprint 1.pdf`, `1.1.pdf` e `1.1.1.pdf`). As três trazem a mesma resposta para a Sprint 1; só `Código da Sprint 1.pdf` continua com a divisão em apps e a Sprint 2. A conversa do Claude (parte da Sprint 1) **não foi revisada**: o link compartilhado não abriu (bloqueio anti-robô) e ela ainda não foi exportada.

## Resumo

O código do Gemini serve como esboço, mas não funciona como está. Os controles de segurança da Sprint 1 não isolam as empresas de fato, e o pipeline de IA da Sprint 2 nunca marca "Erro de Processamento". A implementação desta branch corrige esses pontos, tem 52 testes no backend e 4 no frontend, e o fluxo foi exercitado de ponta a ponta com Postgres, Redis e Celery reais.

## Achados

Severidade: **Crítico** = requisito de segurança violado ou funcionalidade quebrada; **Importante** = requisito não atendido ou bug; **Menor** = qualidade.

### Sprint 1: fundação e segurança

| # | Severidade | Achado | Correção |
|---|---|---|---|
| 1 | Crítico | O RLS nunca é ativado: nada define `app.current_tenant_id`, e o Django conecta como superusuário, que ignora RLS. Sem `FORCE`, o dono da tabela também ignora. | Migration com `ENABLE` + `FORCE` e políticas em avaliação, resposta e pontuação. O tenant é definido por `SET LOCAL` na transação da requisição (`ATOMIC_REQUESTS`). Testes rodam com um papel sem superusuário. |
| 2 | Crítico | `request.user.empresa_id` não existe: não há usuário ligado a empresa. O `IsTenantOwner` compara `None` e bloqueia todos (ou, sem `empresa_id` no objeto, compara com o `id` do próprio objeto). | Usuário customizado `contas.Usuario` com FK para `Empresa`. |
| 3 | Crítico | `has_object_permission` só roda no detalhe: listagens devolvem avaliações de todas as empresas (viola RNF01 e o critério da US02, "todas as queries filtram pelo empresa_id"). | `TenantViewMixin` filtra toda consulta pela empresa do usuário. |
| 4 | Importante | Log de auditoria só no `logger`, sem configuração nem registro persistente (RNF04). | Modelo `AuditoriaAcesso`, gravado por middleware **depois** do rollback da requisição que respondeu 403. |
| 5 | Importante | `SECURE_SSL_REDIRECT = True` fixo quebra o `runserver` local e não considera proxy TLS. | HTTPS/HSTS/cookies seguros ativados quando `DJANGO_DEBUG=false`, com `SECURE_PROXY_SSL_HEADER`. `check --deploy` limpo. |
| 6 | Importante | Versionamento incompleto (US01): versão não é única, nada impede editar perguntas de uma versão já respondida, não existe "arquivar versão anterior". | `versao` única, uma versão ativa por constraint, `publicar()` e `nova_versao()`. A estrutura de uma versão respondida fica travada (inativar pergunta continua permitido). |
| 7 | Importante | Faltam apps registrados, migrations, rotas, serializers, views e testes. | Apps `contas`, `questionarios` e `avaliacoes` completos, API em `/api/v1` (seção 5.3). |
| 8 | Menor | Campos em camelCase (`dataCadastro`, `pesoSistematizacao`), sem validação de pesos. | snake_case (padrão Python/Django) e `CHECK peso > 0`. |
| 9 | Menor | Os models foram divididos em um arquivo por classe e depois reorganizados em apps: duas estruturas propostas na mesma conversa. | Adotada a divisão por apps, com `Questionario`, `Dimensao` e `Pergunta` juntos, como a própria conversa concluiu. |

### Sprint 2: preenchimento, motor e pipeline de IA

| # | Severidade | Achado | Correção |
|---|---|---|---|
| 10 | Crítico | Na task, `import json` fica dentro do `try`: se a primeira chamada ao Ollama der timeout, o `except (..., json.JSONDecodeError)` quebra com `UnboundLocalError` e a retentativa nunca acontece. | Tratamento centralizado em `llm.py`, que converte qualquer falha em `FalhaInferencia`. |
| 11 | Crítico | `self.retry(exc=exc)` relança a exceção original ao estourar o limite, não `MaxRetriesExceededError`: o status `ERRO_PROCESSAMENTO` (RF09) nunca é gravado. | Limite verificado explicitamente antes de retentar; teste cobre a falha persistente. |
| 12 | Importante | Nota da dimensão é soma ponderada sem normalização: cresce com o número de perguntas e é comparada a um corte fixo de 70. | Nota de 0 a 100 normalizada pela escala (1–5) e pelos pesos; índice geral ponderado pelas dimensões (RF05, RF06). |
| 13 | Importante | Dimensão prioritária nunca é desmarcada num recálculo: pode haver duas. Dimensão sem perguntas objetivas recebe 0 e vira "prioritária". | Pontuações recalculadas do zero; dimensões sem objetivas ficam fora do cálculo (RF07). |
| 14 | Importante | Toda retentativa reenvia **todas** as respostas abertas, inclusive as já analisadas, e incrementa `tentativaRetry` em todas. | Cada análise válida é salva na hora; a retentativa só reenvia as pendentes. |
| 15 | Importante | Rascunho (RF04, US03): o endpoint não existe, `Resposta` aceita duplicatas por pergunta, e perguntas de outro questionário ou valores fora da escala são aceitos. | `PATCH /rascunho/` com upsert, `UNIQUE(avaliacao, pergunta)`, validação de pertencimento, tipo e escala. Rascunho único por empresa. |
| 16 | Importante | Status vai para `PROCESSANDO_IA` mesmo sem respostas abertas, e a task nunca é enfileirada. | Submissão calcula a nota e só enfileira a IA (via `on_commit`) se houver texto; responde 202 nesse caso e 200 quando já conclui. |
| 17 | Importante | `Resposta.pergunta` e `PontuacaoDimensao.dimensao` com `CASCADE`: apagar uma pergunta apaga respostas históricas. | `PROTECT`. |
| 18 | Menor | URL e modelo do Ollama fixos no código; prompt concatena o texto do usuário sem delimitação; schema JSON aceita campos extras. | Configuração por variável de ambiente, texto delimitado com instrução para tratá-lo como dado, `additionalProperties: false` e `format` com o schema no Ollama. |
| 19 | Menor | Front usa `axios`, que não é dependência do projeto, tipa respostas como `any`, não envia token e salva a cada tecla sem debounce. | Cliente `fetch` tipado com JWT; auto-save com agrupamento de edições, pausa de 800 ms e retentativa. |

## Implementação

| Requisito | Onde |
|---|---|
| RF01, RF02, US01 (versionamento) | `apps/questionarios/models.py` |
| RF03, RF04, US03 (rascunho) | `apps/avaliacoes/services.py`, `frontend/src/rascunho/`, `frontend/src/paginas/Formulario.tsx` |
| RF05–RF07 (motor determinístico) | `apps/avaliacoes/services.py` → `calcular_pontuacao` |
| RF08–RF10, RNF02, RNF10, RNF11, US04 (IA) | `apps/avaliacoes/llm.py`, `apps/avaliacoes/tasks.py` |
| RNF01, RNF04, US02 (isolamento e auditoria) | `apps/contas/tenancy.py`, `apps/contas/middleware.py`, `apps/avaliacoes/migrations/0003_row_level_security.py` |
| RNF03 (HTTPS) | `config/settings.py` |
| RNF07 (linguagem acessível) | Escala de concordância no formulário |

### Decisões que o grupo precisa validar

- **Escala das objetivas:** 1 a 5 (Discordo totalmente → Concordo totalmente).
- **Nota de corte para "Apta":** 70 (valor do Gemini), configurável em `NOTA_CORTE_APTIDAO`. O documento não define esse valor.
- **Níveis de maturidade:** 5 níveis de 20 pontos cada. O documento cita "nível de maturidade" sem definir as faixas.
- **403 x 404:** o acesso a um recurso de outra empresa responde 403, como pede a US02. Isso revela que o id existe; como os ids são UUID, o risco é baixo.
- **Questionários globais:** o ator Administrador "parametriza conforme a empresa", mas o diagrama de classes não liga `Questionario` a `Empresa`. Foi mantido global, igual ao diagrama.

### Fora do escopo desta entrega

- Conversa do Claude sobre a Sprint 1 (aguardando exportação).
- Renovação automática do token JWT no front: ao expirar (30 min), o usuário volta ao login, e as respostas já estão salvas no rascunho.
- Papel de banco sem superusuário para produção (ver CONTRIBUTING).

## Verificação

- Backend: `python manage.py test apps`, 52 testes. Três testes críticos foram checados por mutação (sem filtro de tenant, sem limite de retentativas, sem RLS em respostas): todos falham com o código quebrado.
- Frontend: `npm test` (4 testes), `tsc -b`, `npm run lint` e `npm run build` limpos.
- Fluxo real com Postgres, Redis e Celery: login, rascunho, submissão (202), notas conferidas à mão (Estratégia 25, Dados 75, Pessoas 100, geral 68,75, nível 4, não apta), retentativa com backoff e `ERRO_PROCESSAMENTO` sem Ollama.
- `manage.py check --deploy` sem avisos com `DJANGO_DEBUG=false`.
