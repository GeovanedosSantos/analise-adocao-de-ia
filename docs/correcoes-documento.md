# Correções para o documento do TCC

Cada item mostra onde fica o trecho, o texto atual e o texto que entra no lugar. A ordem segue o documento.
Premissas aplicadas: o modelo é de **prontidão** (não de maturidade) e **não existe mais status de aptidão**.

Itens que dependem do grupo e não foram preenchidos aqui: os resultados da validação com especialistas (os "X"
do resumo, do abstract e das considerações finais) e as figuras 2 e 3, que precisam ser redesenhadas (item 14).

---

## 1. Abstract — Keywords

As palavras-chave em inglês não batem com as em português e trazem "AI Maturity".

- **Trocar:** `Keywords: Artificial Intelligence; Generative AI; AI Maturity; Technological Diffusion.`
- **Por:** `Keywords: Artificial Intelligence. Literature review. Organizational readiness. Technological diffusion.`

## 2. Quadro 1 — Atores do sistema

**Usuário autenticado**
- **Trocar:** "consulta o catálogo de usos sugeridos e exporta o relatório."
- **Por:** "consulta o catálogo de recomendações e exporta o relatório."

**Administrador**
- **Trocar:** "Responsável por parametrizar as dimensões e perguntas, e gerenciar as versões do questionário."
- **Por:** "Responsável por parametrizar as dimensões, os fatores e as perguntas, gerenciar as versões do questionário e manter o catálogo de recomendações."

## 3. Quadro 2 — Requisitos funcionais

**RF05**
- **Trocar:** "...determinando o nível de prontidão da empresa e seu status final."
- **Por:** "...determinando o nível de prontidão da empresa."

**RF12**
- **Trocar:** "O sistema deve calcular os deltas percentuais de evolução temporal entre diagnósticos históricos consecutivos realizados pela empresa."
- **Por:** "O sistema deve calcular os deltas percentuais de evolução entre diagnósticos consecutivos concluídos pela empresa, para o índice geral e para cada dimensão, como (nota atual − nota anterior) / nota anterior. Quando a nota anterior for zero, o sistema exibe a nota anterior sem a variação."

## 4. Quadro 3 — Requisitos não funcionais

**RNF08**
- **Trocar:** "As perguntas, pesos e sugestões do catálogo de casos de uso devem ser parametrizáveis..."
- **Por:** "As perguntas, os pesos e as recomendações do catálogo devem ser parametrizáveis..."

## 5. Casos de uso

**UC02 — Exceções** (os passos citados não batiam com o fluxo principal)
- **Trocar:** "E01 - Perguntas obrigatórias não respondidas (passo 7)"
- **Por:** "E01 - Perguntas obrigatórias não respondidas (passo 6)"
- **Trocar:** "E03 - Falha no Motor de avaliação (passo 9): o sistema exibe uma mensagem de erro, mantém as respostas registradas e retenta automáticamente (RNF10)."
- **Por:** "E03 - Falha no motor de avaliação (passo 8): o sistema exibe uma mensagem de erro, mantém as respostas registradas e tenta novamente de forma automática (RNF10)."

**UC06 — Exceções**
- **Trocar:** "sistema informa que não há recomendações cadastradas0."
- **Por:** "sistema informa que não há recomendações cadastradas."

**UC08 — FA01**
- **Trocar:** "3.3 Administrador altera e confima;"
- **Por:** "3.3 Administrador altera e confirma;"

**UC09 — Fluxo principal, passo 4**
- **Trocar:** "Sistema solicita enunciado, dimensão associada, tipo de resposta e tipo de pergunta;"
- **Por:** "Sistema solicita enunciado, dimensão e fator associados, tipo de resposta e tipo de pergunta;"

**UC11 — FA02, passo 3.4**
- **Trocar:** "3.4 Sistema inativa, deixando de ser associada a resultados novos);"
- **Por:** "3.4 Sistema inativa a recomendação, que deixa de ser associada a resultados novos;"

**UC12 — Fluxo principal, passos 2 a 5**
- **Trocar:** "2. Sistema de inferência recebe as pontuações e pesos por dimensão, e as recomendações aplicáveis;"
- **Por:** "2. Sistema de inferência recebe as pontuações e os pesos por dimensão e as recomendações aplicáveis, já selecionadas pelas faixas de pontuação;"

**UC12 — Exceções** (os passos citados não batiam com o fluxo principal)
- **Trocar:** "E01 - Nenhuma recomendação aplicável (passo 3)"
- **Por:** "E01 - Nenhuma recomendação aplicável (passo 2)"
- **Trocar:** "E02 - Falha na análise qualitativa (passo 4)"
- **Por:** "E02 - Falha na análise qualitativa ou no ranqueamento (passos 3 e 4)"

**Sumário**
- **Trocar:** "2.4.12 UC12- Fazer recomendações"
- **Por:** "2.4.12 UC12 - Fazer recomendações" (e o mesmo no título da seção)

## 6. Histórias de usuário

**US08 — Critérios de aceite**
- **Trocar:** "O relatório deve conter o índice geral, a pontuação por dimensão, o status final de aptidão e as recomendações para aumentar a prontidão."
- **Por:** "O relatório deve conter o índice geral, o nível de prontidão, a pontuação por dimensão, os gráficos comparativos e as recomendações para aumentar a prontidão."

## 7. Quadro 5 — Divisão das sprints (substituir a coluna de entregáveis)

As referências estavam com a numeração antiga de US e RF (havia RF17, que não existe). Ficam assim:

**Sprint 1: Fundação & Segurança**
- Configuração da infraestrutura inicial e banco PostgreSQL com isolamento lógico estrito entre tenants via Row-Level Security (RLS) (RNF01);
- Modelagem Django para suporte a questionários estruturados, versionados e parametrizáveis (US09, RF01, RF02, RNF08);
- Implementação da camada de segurança com autenticação JWT, bloqueio de requisições entre tenants via HTTP 403 (Forbidden) e registro em log de auditoria (RNF04);
- Criptografia em trânsito aplicada em todas as rotas via HTTPS/TLS (RNF03).

**Sprint 2: Preenchimento Dinâmico, Motor Determinístico & Pipeline de IA**
- Interface dinâmica em React/TypeScript para captura de respostas objetivas e abertas, com linguagem acessível a gestores e salvamento automático e recuperação de rascunhos (US01, RF01, RF03, RF04, RNF07);
- Implementação do motor de pontuação determinística: cálculo da prontidão por dimensão, nível de prontidão, índice geral ponderado e identificação da dimensão prioritária (US02, US03, US04, RF05, RF06, RF07);
- Configuração da mensageria e das filas de tarefas assíncronas (Celery/Redis) para desacoplar a inferência sem travar a interface (US05, RF08, RNF06);
- Integração local com Ollama/vLLM, sem envio de dados para serviços em nuvem, com validação rigorosa de contratos JSON, retentativas com backoff exponencial para timeouts e descarte com nova inferência para respostas fora do schema (US05, RF08, RF09, RNF02, RNF10, RNF11).

**Sprint 3: Dashboards Analíticos, Catálogo & Relatórios em PDF**
- Endpoints da API para consulta do histórico cronológico de diagnósticos e cálculo dos deltas percentuais entre avaliações consecutivas (US07, RF11, RF12, RNF05);
- Dashboards responsivos no front-end (desktop e tablet): gráfico de radar multicamadas comparativo e gráfico de linha do tempo (US07, RF13, RF14, RNF12);
- Catálogo dinâmico de recomendações compatível com o nível de prontidão e com as notas de cada dimensão (US06, US10, RF10);
- Serviço de geração e download de relatórios em PDF com WeasyPrint, padronização visual entre leitores e dispositivos, meta de até 5 segundos e tratamento de falhas (US08, RF15, RF16, RNF09, RNF13).

**Sprint 4: Release & Homologação**
- Testes de carga e concorrência nos workers Celery e na inferência local de IA (RNF06, RNF10);
- Medição de desempenho para garantir resposta das rotas síncronas abaixo de 500 ms e geração de PDF em até 5 segundos (RNF05, RNF09);
- Testes de segurança do isolamento multi-tenant (RLS) e verificação dos logs de acessos não autorizados (RNF01, RNF04);
- Homologação ponta a ponta dos fluxos de avaliação, refinamento de UI/UX responsiva e empacotamento final da release (RF01 a RF16, RNF01 a RNF13).

## 8. Seção 4.1 — Diagrama de classes (texto)

**Segundo parágrafo** (só as respostas objetivas são obrigatórias)
- **Trocar:** "O rascunho só será salvo quando houver pelo menos uma resposta na avaliação e todas as respostas precisam estar presentes para a avaliação ser concluída."
- **Por:** "O rascunho só será salvo quando houver pelo menos uma resposta na avaliação, e todas as respostas objetivas precisam estar presentes para a avaliação ser enviada; as respostas abertas são opcionais."

**Acrescentar ao fim do segundo parágrafo**
> A avaliação também é composta pela classe RecomendacaoAvaliacao, que registra as até 10 recomendações do catálogo escolhidas para o plano de ação e a posição de cada uma. Como as recomendações só são escolhidas no envio, uma avaliação pode ter de 0 a 10 (0..10) instâncias de RecomendacaoAvaliacao.

**Terceiro parágrafo**
- **Trocar:** "O questionário é composto por 1 ou mais (1..*) instâncias de Perguntas, cujas dimensões definem as dimensões daquela instância de questionário, e, consequentemente, 1 ou mais (1..*) instâncias de Dimensao. A classe CasoDeUso representa um caso de uso (IA) para a sua dimensão associada. Cada dimensão pode ter 0 ou mais (0..*) casos de uso."
- **Por:** "O questionário é composto por 1 ou mais (1..*) instâncias de Dimensao. Cada dimensão agrupa 1 ou mais (1..*) instâncias de Fator, que representam os fatores de prontidão do modelo, e cada pergunta pertence a uma dimensão e a um fator. A classe Recomendacao representa uma ação do catálogo, ligada a uma dimensão pelo código da dimensão e aplicável a uma faixa de pontuação; cada dimensão pode ter 0 ou mais (0..*) recomendações."

**Quarto parágrafo**
- **Trocar:** "inferência via LLM, catálogo de casos de uso, histórico de pontuação e deltas de evolução"
- **Por:** "inferência via LLM, seleção e ranqueamento das recomendações, histórico de pontuação e deltas de evolução"

## 9. Seção 5.3 — Padrões e boas práticas

Nenhuma troca necessária: todos os itens agora estão implementados. Opcionalmente, acrescentar ao item de uso controlado da LLM: "a versão dos prompts fica registrada em cada avaliação".

## 10. Seção 6 — Novo parágrafo sobre o cálculo e os níveis de prontidão

O documento não define as faixas dos níveis nem os pesos. Sugestão de parágrafo (no fim da seção 6.3.5 ou numa nova seção 6.3.6, renumerando Limitações para 6.3.7):

> O questionário mede os 19 fatores com 38 itens em escala Likert de 5 pontos, dois por fator, e uma pergunta aberta por dimensão. A nota de cada dimensão é a média ponderada dos itens, convertida para a escala de 0 a 100. O índice geral é a média das dimensões ponderada pelos pesos de cada uma; nesta versão, os pesos são proporcionais ao número de fatores de cada dimensão (Tecnologia 3, Organização 5, Dados 3, Conhecimento 3 e Estratégia 5). O índice geral determina o nível de prontidão em cinco faixas de 20 pontos: nível 1 (0 a 19,9), nível 2 (20 a 39,9), nível 3 (40 a 59,9), nível 4 (60 a 79,9) e nível 5 (80 a 100). A dimensão de menor nota é indicada como ponto de partida do plano de ação; em caso de empate, prevalece a de maior peso.

Os itens usados hoje no sistema estão em `backend/apps/questionarios/modelo_prontidao.py`, marcados como provisórios até a validação com especialistas.

## 11. Seção 6.1.1

- **Trocar (3 ocorrências):** "TORNATZSKY; FLEISCHER"
- **Por:** "TORNATZKY; FLEISCHER"

## 12. Seção 6.1.2

- **Trocar:** "características da estrutura organizacional internal"
- **Por:** "características da estrutura organizacional interna"
- **Trocar:** "sua atitude em relação à mudanças"
- **Por:** "sua atitude em relação a mudanças"

## 13. Seção 6.3.4

O Quadro 11 é o dos fatores mantidos; não existe quadro com os quatro critérios.

- **Trocar:** "O Quadro 11 resume a aplicação desses critérios."
- **Por:** "A aplicação desses critérios a cada dimensão é descrita a seguir."

## 14. Figuras

- **Figura 2 (diagrama de classes):** incluir Fator (Dimensao 1 — 1..* Fator; Fator 1 — 0..* Pergunta), Recomendacao no lugar de CasoDeUso e RecomendacaoAvaliacao (Avaliacao 1 — 0..10 RecomendacaoAvaliacao; Recomendacao 1 — 0..* RecomendacaoAvaliacao). Em Avaliacao, o atributo é `nivel_prontidao` e não existe atributo de aptidão.
- **Figura 3 (diagrama de sequência):** depois do cálculo da pontuação, incluir a seleção das recomendações pelas faixas e, no worker, o ranqueamento pela LLM. Em caso de falha, o status vai para "Erro de processamento" e o plano fica na ordem das faixas.
