import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint

logger = logging.getLogger("AIModelEngine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==============================================================================
# CONFIGURAÇÕES DE NUVEM E BANCO DE DADOS (VARIÁVEIS DE AMBIENTE)
# ==============================================================================
# O Backend pode sobrescrever estas variáveis no arquivo .env do ambiente de produção/hospedagem:
DB_CATALOGO_TABELA = os.getenv("DB_CATALOGO_TABELA", "catalogo_recomendacoes")
# Exemplos para string de conexão com banco de dados:
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/tcc_db")

# ==============================================================================
# GRUPO 1: PARÂMETROS E TAXONOMIA DO MODELO (FUNDAMENTAÇÃO TEÓRICA)
# ==============================================================================
PESOS_DIMENSOES: Dict[str, float] = {
    "tecnologia": 0.25,   # Alsheibani et al. (2020) / Mikalef & Gupta (2021)
    "organizacao": 0.20,  # Jöhnk et al. (2021) / Alsheibani et al. (2020)
    "dados": 0.25,        # Mikalef & Gupta (2021) - RBV Data Assets
    "conhecimento": 0.15, # Mikalef & Gupta (2021) - Human Skills
    "estrategia": 0.15    # Jöhnk et al. (2021) - Strategic Alignment
}

SUBDIMENSOES_MAPA: Dict[str, List[str]] = {
    "tecnologia": ["infraestrutura_cloud", "sistemas_legados", "ferramental_mlops"],
    "organizacao": ["suporte_lideranca", "cultura_risco", "governanca_etica"],
    "dados": ["qualidade_saneamento", "arquitetura_acessibilidade", "governanca_dados"],
    "conhecimento": ["habilidades_tecnicas", "literacia_negocio", "programas_upskilling"],
    "estrategia": ["casos_uso_roi", "orcamento_priorizacao", "escalabilidade_modelo"]
}

LikertScore = conint(ge=1, le=5)


# ==============================================================================
# GRUPO 2: CATÁLOGO DE RECOMENDAÇÕES (INTERFACE PARA BANCO DE DADOS)
# ==============================================================================
class RecomendacaoCatalogoItem(BaseModel):
    id_recomendacao: str = Field(..., description="ID único no Banco de Dados")
    subdimensao: str = Field(..., description="Sub-dimensão vinculada ex: 'tecnologia.sistemas_legados'")
    faixas_score_aplicaveis: List[str] = Field(..., description="Faixas de score (ex: 'critico' <= 40, 'intermediario' 40-70)")
    acao_padronizada: str = Field(..., description="Texto base da recomendação curada pelos especialistas")
    fase_sugerida: str = Field(..., description="Curto Prazo, Médio Prazo ou Longo Prazo")
    prioridade_default: str = Field(..., description="Alta, Média ou Baixa")
    esforco_default: str = Field(..., description="Baixo, Médio ou Alto")
    impacto_default: str = Field(..., description="Alto, Médio ou Baixo")
    kpi_sugerido: str = Field(..., description="Métrica de sucesso predefinida")


class CatalogoRecomendacoesRepository:
    """
    Repositório de acesso ao Catálogo de Recomendações.
    Nesta etapa de prototipação, mantemos o catálogo mockado em memória.
    """
    @staticmethod
    async def buscar_recomendacoes_por_subdimensoes(subdimensoes_com_score: Dict[str, float]) -> List[RecomendacaoCatalogoItem]:
        
        # ----------------------------------------------------------------------
        # 📍 PONTO DE INTEGRAÇÃO COM BANCO DE DADOS PELO BACKEND (SQL / ORM)
        # ----------------------------------------------------------------------
        # O time de Backend deve substituir este método ou descomentar a lógica abaixo
        # para consultar a tabela definida em DB_CATALOGO_TABELA.
        #
        # EXEMPLO COM SQLALCHEMY / ASYNCPG / PRISMA:
        #
        # async with db_session() as session:
        #     query = f"SELECT * FROM {DB_CATALOGO_TABELA} WHERE subdimensao IN :subdims"
        #     results = await session.execute(query, {"subdims": tuple(subdimensoes_com_score.keys())})
        #     ...
        # ----------------------------------------------------------------------

        # Catálogo MOCK em memória para testes (Usado enquanto o Banco não está conectado)
        catalogo_mock: List[RecomendacaoCatalogoItem] = [
            # --- TECNOLOGIA ---
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_TEC_LEG_01",
                subdimensao="tecnologia.sistemas_legados",
                faixas_score_aplicaveis=["critico"],
                acao_padronizada="Construir uma camada de middleware/API Gateway para encapsular os sistemas legados e viabilizar integrações em tempo real.",
                fase_sugerida="Curto Prazo (0-3 meses)",
                prioridade_default="Alta",
                esforco_default="Médio",
                impacto_default="Alto",
                kpi_sugerido="100% dos fluxos de dados críticos expostos via APIs seguras"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_TEC_MLOPS_01",
                subdimensao="tecnologia.ferramental_mlops",
                faixas_score_aplicaveis=["critico", "intermediario"],
                acao_padronizada="Implantar esteira básica de MLOps com versionamento de modelos, registro de experimentos e monitoramento de data drift.",
                fase_sugerida="Médio Prazo (3-6 meses)",
                prioridade_default="Alta",
                esforco_default="Alto",
                impacto_default="Alto",
                kpi_sugerido="Redução de 50% no tempo de deploy de modelos para produção"
            ),
            # --- DADOS ---
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_DAD_QUAL_01",
                subdimensao="dados.qualidade_saneamento",
                faixas_score_aplicaveis=["critico"],
                acao_padronizada="Estabelecer pipeline automatizado de validação de qualidade de dados (Data Profiling e Cleansing) nas fontes primárias.",
                fase_sugerida="Curto Prazo (0-3 meses)",
                prioridade_default="Alta",
                esforco_default="Médio",
                impacto_default="Alto",
                kpi_sugerido="Atingir 95% de completude e consistência na base de dados de treino"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_DAD_GOV_01",
                subdimensao="dados.governanca_dados",
                faixas_score_aplicaveis=["critico", "intermediario"],
                acao_padronizada="Implementar catálogo de dados com políticas claras de controle de acesso por perfil e catalogação de linhagem de dados.",
                fase_sugerida="Médio Prazo (3-6 meses)",
                prioridade_default="Média",
                esforco_default="Médio",
                impacto_default="Alto",
                kpi_sugerido="100% dos ativos de dados para IA catalogados e em conformidade com LGPD"
            ),
            # --- CONHECIMENTO ---
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_CON_UPS_01",
                subdimensao="conhecimento.programas_upskilling",
                faixas_score_aplicaveis=["critico"],
                acao_padronizada="Lançar programa interno de alfabetização em IA (AI Literacy) focado nas equipes de produto e operações.",
                fase_sugerida="Curto Prazo (0-3 meses)",
                prioridade_default="Alta",
                esforco_default="Baixo",
                impacto_default="Alto",
                kpi_sugerido="80% das equipes operacionais certificadas no treinamento básico de IA"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_CON_TEC_01",
                subdimensao="conhecimento.habilidades_tecnicas",
                faixas_score_aplicaveis=["critico", "intermediario"],
                acao_padronizada="Contratar ou capacitar especialistas em Engenharia de Prompt e Fine-tuning de modelos para fortalecer o time de TI.",
                fase_sugerida="Médio Prazo (3-6 meses)",
                prioridade_default="Média",
                esforco_default="Médio",
                impacto_default="Alto",
                kpi_sugerido="Redução na dependência de consultorias externas para sustentação de modelos"
            ),
            # --- ORGANIZAÇÃO ---
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_ORG_RIS_01",
                subdimensao="organizacao.cultura_risco",
                faixas_score_aplicaveis=["critico", "intermediario"],
                acao_padronizada="Criar um Comitê Multidisciplinar de Governança Ética e Gestão de Risco de IA com alocação de verba para PoCs exploratórias.",
                fase_sugerida="Curto Prazo (0-3 meses)",
                prioridade_default="Média",
                esforco_default="Baixo",
                impacto_default="Médio",
                kpi_sugerido="Tempo de avaliação de novos casos de uso reduzido para menos de 10 dias úteis"
            ),
            # --- ESTRATÉGIA ---
            RecomendacaoCatalogoItem(
                id_recomendacao="REC_EST_ROI_01",
                subdimensao="estrategia.casos_uso_roi",
                faixas_score_aplicaveis=["critico", "intermediario"],
                acao_padronizada="Mapear a matriz de casos de uso com metodologia estruturada de cálculo de ROI antes de aprovar novos desenvolvimentos.",
                fase_sugerida="Longo Prazo (6-12+ meses)",
                prioridade_default="Média",
                esforco_default="Médio",
                impacto_default="Alto",
                kpi_sugerido="100% dos projetos de IA em produção com ROI mensurado trimestralmente"
            )
        ]

        # Filtragem dinâmica conforme as notas das subdimensões da empresa
        itens_selecionados: List[RecomendacaoCatalogoItem] = []
        for sub_key, score in subdimensoes_com_score.items():
            categoria_score = "critico" if score < 40.0 else ("intermediario" if score < 70.0 else "avancado")
            for item in catalogo_mock:
                if item.subdimensao == sub_key and categoria_score in item.faixas_score_aplicaveis:
                    itens_selecionados.append(item)

        return itens_selecionados


# ==============================================================================
# GRUPO 3: CONTRATO DE DADOS E SCHEMAS PYDANTIC
# ==============================================================================
class HealthCheckOutput(BaseModel):
    status: str = Field(..., description="Status do microserviço ('healthy' ou 'degraded')")
    ollama_status: str = Field(..., description="Status da conexão com LLM ('connected' ou 'unreachable')")
    modelo_ativo: str = Field(..., description="Nome do modelo de linguagem configurado")
    versao_api: str = Field("1.4.0", description="Versão atualizada do serviço")


class ModelInputPayload(BaseModel):
    empresa_nome: str = Field(..., description="Nome da organização avaliada", min_length=2)
    contexto_qualitativo: Optional[str] = Field(None, description="Observações textuais gerais")
    respostas: Dict[str, Dict[str, List[LikertScore]]] = Field(
        ...,
        description="Respostas objetivas organizadas por Dimensão e Sub-dimensão"
    )
    respostas_dissertativas: Optional[Dict[str, str]] = Field(
        default=None,
        description="Respostas abertas/qualitativas por dimensão"
    )


class ItemPlanoAcao(BaseModel):
    id_catalogo: str = Field(..., description="Chave/ID de referência no catálogo do banco de dados")
    fase: str = Field(..., description="Curto Prazo (0-3 meses), Médio Prazo (3-6 meses), Longo Prazo (6-12+ meses)")
    acao: str = Field(..., description="Ação padronizada vinda do catálogo de recomendações")
    dimensao_foco: str = Field(..., description="Sub-dimensão tratada ex: 'tecnologia.sistemas_legados'")
    prioridade: str = Field("Alta", description="Nível de prioridade: 'Alta', 'Média' ou 'Baixa'")
    esforco_estimado: str = Field("Médio", description="Esforço de implementação: 'Baixo', 'Médio' ou 'Alto'")
    impacto_esperado: str = Field("Alto", description="Impacto esperado no negócio: 'Alto', 'Médio' ou 'Baixo'")
    kpi_sucesso: Optional[str] = Field(None, description="Métrica/KPI para mensurar o sucesso da ação")


class RelatorioDiagnosticoLLM(BaseModel):
    diagnostico_geral: str = Field(..., description="Parecer executivo do estado de prontidão")
    resumo_executivo_clevel: str = Field(..., description="Síntese direcionada à tomada de decisão da alta gestão")
    nivel_risco_implantacao: str = Field("Médio", description="Avaliação de risco: 'Baixo', 'Médio', 'Alto' ou 'Crítico'")
    pontos_fortes: List[str] = Field(..., description="Pontos fortes identificados")
    gaps_criticos: List[str] = Field(..., description="Gargalos críticos identificados por sub-dimensão")
    plano_de_acao: List[ItemPlanoAcao] = Field(..., description="Plano de ação filtrado e ordenado a partir do Catálogo do Banco de Dados")


class ModelEvaluationOutput(BaseModel):
    score_geral: float = Field(..., description="Score global de prontidão (0 a 100)")
    scores_dimensoes: Dict[str, float] = Field(..., description="Scores por dimensão principal (0 a 100)")
    scores_subdimensoes: Dict[str, float] = Field(..., description="Scores por sub-dimensão (0 a 100)")
    tempo_execucao_ms: float = Field(..., description="Tempo de processamento da requisição em ms")
    relatorio_llm: RelatorioDiagnosticoLLM = Field(..., description="Diagnóstico qualitativo vinculado ao catálogo")


class SchemaDetalhadoOutput(BaseModel):
    pesos_dimensoes: Dict[str, float] = Field(..., description="Pesos aplicados às dimensões")
    subdimensoes_mapa: Dict[str, List[str]] = Field(..., description="Sub-dimensões cadastradas por dimensão")
    escala_likert: Dict[str, int] = Field(..., description="Intervalo da escala Likert")


# ==============================================================================
# GRUPO 4: ENGINE DETERMINÍSTICA DE CÁLCULO
# ==============================================================================
class ScoreEngine:
    @classmethod
    def validar_taxonomia_payload(cls, respostas: Dict[str, Dict[str, List[int]]]) -> Optional[str]:
        for dim, subdims_obr in SUBDIMENSOES_MAPA.items():
            if dim not in respostas:
                return f"Dimensão principal ausente no payload: '{dim}'."
            for sub_obr in subdims_obr:
                if sub_obr not in respostas[dim]:
                    return f"Sub-dimensão obrigatória ausente no payload: '{dim}.{sub_obr}'."
        return None

    @classmethod
    def processar_pontuacoes(
        cls, 
        respostas: Dict[str, Dict[str, List[int]]]
    ) -> Tuple[float, Dict[str, float], Dict[str, float]]:
        scores_subdimensoes: Dict[str, float] = {}
        scores_dimensoes: Dict[str, float] = {}
        score_ponderado_total: float = 0.0

        for dim_key, subdims in respostas.items():
            subdim_scores_lista: List[float] = []
            
            for sub_key, notas in subdims.items():
                if not notas:
                    scores_subdimensoes[f"{dim_key}.{sub_key}"] = 0.0
                    continue
                
                media_likert = sum(notas) / len(notas)
                nota_sub_100 = round(((media_likert - 1.0) / 4.0) * 100.0, 2)
                
                scores_subdimensoes[f"{dim_key}.{sub_key}"] = nota_sub_100
                subdim_scores_lista.append(nota_sub_100)

            if subdim_scores_lista:
                nota_dim_100 = round(sum(subdim_scores_lista) / len(subdim_scores_lista), 2)
            else:
                nota_dim_100 = 0.0

            scores_dimensoes[dim_key] = nota_dim_100
            peso = PESOS_DIMENSOES.get(dim_key, 0.20)
            score_ponderado_total += nota_dim_100 * peso

        score_geral = round(score_ponderado_total, 2)

        return score_geral, scores_dimensoes, scores_subdimensoes


# ==============================================================================
# GRUPO 5: ORQUESTRADOR DO LLM COM ANCORAGEM NO CATÁLOGO
# ==============================================================================
class LLMOrchestrator:
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        model_name: Optional[str] = None
    ):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "llama3.2")

    async def verificar_health(self, client: httpx.AsyncClient) -> bool:
        try:
            resp = await client.get(f"{self.base_url}/api/version", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def _construir_prompt_com_catalogo(
        self,
        empresa: str,
        score: float,
        dim_scores: dict,
        subdim_scores: dict,
        contexto: Optional[str],
        respostas_dissertativas: Optional[Dict[str, str]],
        recomendacoes_catalogo: List[RecomendacaoCatalogoItem]
    ) -> str:
        catalogo_json_prompt = [
            {
                "id_catalogo": item.id_recomendacao,
                "dimensao_foco": item.subdimensao,
                "acao": item.acao_padronizada,
                "fase": item.fase_sugerida,
                "prioridade": item.prioridade_default,
                "esforco_estimado": item.esforco_default,
                "impacto_esperado": item.impacto_default,
                "kpi_sucesso": item.kpi_sugerido
            }
            for item in recomendacoes_catalogo
        ]

        dissertativas_formatted = (
            json.dumps(respostas_dissertativas, ensure_ascii=False) 
            if respostas_dissertativas else "Nenhum relato dissertativo fornecido."
        )

        return f"""Você é um auditor sênior em Prontidão Organizacional para Adoção de IA.
Sua missão é emitir um diagnóstico executivo e SELECIONAR as recomendações mais adequadas a partir do CATÁLOGO PRÉ-APROVADO DO BANCO DE DADOS.

[DADOS QUANTITATIVOS DA EMPRESA]
- Empresa: {empresa}
- Score Geral: {score}/100
- Scores por Dimensão Principal: {json.dumps(dim_scores, ensure_ascii=False)}
- Scores Granulares por Sub-Dimensão: {json.dumps(subdim_scores, ensure_ascii=False)}

[RELATOS DISSERTATIVOS DA EMPRESA]
- Observação Geral: "{contexto or 'Sem observações.'}"
- Detalhes por Dimensão: {dissertativas_formatted}

[CATÁLOGO DISPONÍVEL NO BANCO DE DADOS FORNECIDO]
{json.dumps(catalogo_json_prompt, ensure_ascii=False, indent=2)}

[REGRAS OBRIGATÓRIAS PARA O PLANO DE AÇÃO]
1. O `plano_de_acao` DEVE ser composto EXCLUSIVAMENTE por itens extraídos do [CATÁLOGO DISPONÍVEL NO BANCO DE DADOS].
2. Não invente novas ações para o plano de ação; mantenha rigorosamente o `id_catalogo`, `acao`, `dimensao_foco` e `kpi_sucesso` vindos do catálogo.
3. Você pode ordenar os itens e ajustar a `prioridade` ou `fase` caso os relatos dissertativos indiquem urgência maior.
4. Forneça um `resumo_executivo_clevel` focado na tomada de decisão da alta gestão.
5. Classifique o `nivel_risco_implantacao` ('Baixo', 'Médio', 'Alto' ou 'Crítico').

Responda EXCLUSIVAMENTE um objeto JSON válido alinhado ao schema fornecido."""

    async def gerar_diagnostico(
        self,
        client: httpx.AsyncClient,
        empresa_nome: str,
        score_geral: float,
        scores_dimensoes: dict,
        scores_subdimensoes: dict,
        recomendacoes_catalogo: List[RecomendacaoCatalogoItem],
        contexto: Optional[str] = None,
        respostas_dissertativas: Optional[Dict[str, str]] = None
    ) -> RelatorioDiagnosticoLLM:
        prompt = self._construir_prompt_com_catalogo(
            empresa=empresa_nome,
            score=score_geral,
            dim_scores=scores_dimensoes,
            subdim_scores=scores_subdimensoes,
            contexto=contexto,
            respostas_dissertativas=respostas_dissertativas,
            recomendacoes_catalogo=recomendacoes_catalogo
        )

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": RelatorioDiagnosticoLLM.model_json_schema(),
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 1024
            }
        }

        try:
            response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "{}")
                return RelatorioDiagnosticoLLM(**json.loads(response_text))
            else:
                logger.warning(f"LLM Provider retornou status {response.status_code}. Executando Fallback de Catálogo.")
                return self._gerar_fallback_catalogo(score_geral, recomendacoes_catalogo)
        except Exception as e:
            logger.error(f"Erro/Timeout na comunicação com LLM ({str(e)}). Executando Fallback de Catálogo.")
            return self._gerar_fallback_catalogo(score_geral, recomendacoes_catalogo)

    def _gerar_fallback_catalogo(
        self,
        score_geral: float,
        recomendacoes_catalogo: List[RecomendacaoCatalogoItem]
    ) -> RelatorioDiagnosticoLLM:
        plano_fallback: List[ItemPlanoAcao] = []
        for item in recomendacoes_catalogo[:3]:
            plano_fallback.append(
                ItemPlanoAcao(
                    id_catalogo=item.id_recomendacao,
                    fase=item.fase_sugerida,
                    acao=item.acao_padronizada,
                    dimensao_foco=item.subdimensao,
                    prioridade=item.prioridade_default,
                    esforco_estimado=item.esforco_default,
                    impacto_esperado=item.impacto_default,
                    kpi_sucesso=item.kpi_sugerido
                )
            )

        return RelatorioDiagnosticoLLM(
            diagnostico_geral=f"Diagnóstico automatizado (Fallback): A organização obteve score global de {score_geral}/100.",
            resumo_executivo_clevel="Recomendamos priorizar a mitigação dos gargalos mapeados no catálogo do banco de dados com base na pontuação atingida.",
            nivel_risco_implantacao="Alto" if score_geral < 50 else ("Médio" if score_geral < 75 else "Baixo"),
            pontos_fortes=["Processamento quantitativo executado com sucesso."],
            gaps_criticos=["Gargalos identificados e vinculados ao catálogo de recomendações curadas."],
            plano_de_acao=plano_fallback
        )


# ==============================================================================
# GRUPO 6: LIFESPAN E ROTAS FASTAPI (SERVIÇO PRINCIPAL)
# ==============================================================================
http_client: Optional[httpx.AsyncClient] = None
llm_orchestrator = LLMOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=35.0, limits=httpx.Limits(max_keepalive_connections=10, max_connections=20))
    logger.info(f"Pool HTTP inicializado. LLM apontando para: {llm_orchestrator.base_url} (Modelo: {llm_orchestrator.model_name})")
    logger.info(f"Tabela do Catálogo no Banco de Dados configurada como: '{DB_CATALOGO_TABELA}'")
    yield
    await http_client.aclose()
    logger.info("Pool de conexões HTTP do AI Model Service encerrado.")

app = FastAPI(
    title="AI Readiness Model Service",
    version="1.4.0",
    description="Microserviço otimizado com Engine de Scores e Integração com Catálogo de Recomendações em Banco de Dados.",
    lifespan=lifespan
)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/model/health", response_model=HealthCheckOutput)
async def verificar_saude_servico():
    ollama_ok = await llm_orchestrator.verificar_health(http_client)
    return HealthCheckOutput(
        status="healthy" if ollama_ok else "degraded",
        ollama_status="connected" if ollama_ok else "unreachable",
        modelo_ativo=llm_orchestrator.model_name
    )


@app.get("/api/v1/model/schema", response_model=SchemaDetalhadoOutput)
async def obter_schema_modelo():
    return SchemaDetalhadoOutput(
        pesos_dimensoes=PESOS_DIMENSOES,
        subdimensoes_mapa=SUBDIMENSOES_MAPA,
        escala_likert={"min": 1, "max": 5}
    )


@app.post("/api/v1/model/evaluate", response_model=ModelEvaluationOutput)
async def executar_avaliacao_modelo(
    payload: ModelInputPayload,
    dry_run: bool = Query(
        False, 
        description="Se True, executa cálculo em <10ms com relatório simulado usando o catálogo sem chamar o LLM."
    )
):
    inicio_tempo = time.perf_counter()
    try:
        # 1. Validação Pré-flight da Taxonomia
        erro_taxonomia = ScoreEngine.validar_taxonomia_payload(payload.respostas)
        if erro_taxonomia:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Falha na taxonomia do payload: {erro_taxonomia}"
            )

        # 2. Processamento determinístico otimizado
        score_geral, scores_dimensoes, scores_subdimensoes = ScoreEngine.processar_pontuacoes(payload.respostas)

        # 3. Consulta ao Catálogo de Recomendações (Simulando consulta ao Banco de Dados)
        recomendacoes_catalogo = await CatalogoRecomendacoesRepository.buscar_recomendacoes_por_subdimensoes(scores_subdimensoes)

        # 4. Execução: Dry-Run ou LLM completo
        if dry_run:
            relatorio_llm = llm_orchestrator._gerar_fallback_catalogo(
                score_geral=score_geral,
                recomendacoes_catalogo=recomendacoes_catalogo
            )
            relatorio_llm.diagnostico_geral = f"[MODO DRY-RUN SIMULADO] Diagnóstico ancorado no catálogo do Banco de Dados para {payload.empresa_nome}."
        else:
            relatorio_llm = await llm_orchestrator.gerar_diagnostico(
                client=http_client,
                empresa_nome=payload.empresa_nome,
                score_geral=score_geral,
                scores_dimensoes=scores_dimensoes,
                scores_subdimensoes=scores_subdimensoes,
                recomendacoes_catalogo=recomendacoes_catalogo,
                contexto=payload.contexto_qualitativo,
                respostas_dissertativas=payload.respostas_dissertativas
            )

        tempo_execucao_ms = round((time.perf_counter() - inicio_tempo) * 1000.0, 2)

        return ModelEvaluationOutput(
            score_geral=score_geral,
            scores_dimensoes=scores_dimensoes,
            scores_subdimensoes=scores_subdimensoes,
            tempo_execucao_ms=tempo_execucao_ms,
            relatorio_llm=relatorio_llm
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no processamento do modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento do modelo de IA: {str(e)}"
        )