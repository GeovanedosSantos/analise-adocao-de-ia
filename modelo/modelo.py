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
# CONFIGURAÇÕES DE AMBIENTE
# ==============================================================================
DB_CATALOGO_TABELA = os.getenv("DB_CATALOGO_TABELA", "catalogo_recomendacoes")

# ==============================================================================
# TAXONOMIA DO MODELO (37 PERGUNTAS / 19 SUB-DIMENSÕES)
# ==============================================================================
SUBDIMENSOES_MAPA: Dict[str, List[str]] = {
    "tecnologia": [
        "infraestrutura_cloud", 
        "sistemas_legados", 
        "ferramental_mlops", 
        "vantagem_complexidade"
    ],
    "organizacao": [
        "suporte_lideranca", 
        "cultura_risco", 
        "governanca_etica", 
        "colaboracao_interareas", 
        "processos_fluxos", 
        "gestao_mudanca"
    ],
    "dados": [
        "qualidade_saneamento", 
        "arquitetura_acessibilidade", 
        "governanca_dados"
    ],
    "conhecimento": [
        "habilidades_tecnicas", 
        "literacia_negocio", 
        "programas_upskilling"
    ],
    "estrategia": [
        "casos_uso_roi", 
        "orcamento_priorizacao", 
        "escalabilidade_modelo", 
        "visao_plano_ia", 
        "adequacao_processos"
    ]
}

# Cálculo dinâmico do peso relativo das dimensões (100% / n dimensões)
_num_dimensoes = len(SUBDIMENSOES_MAPA)
PESOS_DIMENSOES: Dict[str, float] = {
    dim: round(1.0 / _num_dimensoes, 4) for dim in SUBDIMENSOES_MAPA.keys()
}

LikertScore = conint(ge=1, le=5)


# ==============================================================================
# SCHEMAS DO CATÁLOGO E REPOSITÓRIO
# ==============================================================================
class RecomendacaoCatalogoItem(BaseModel):
    id_recomendacao: int = Field(..., description="ID sequencial no Banco de Dados")
    id_pergunta: str = Field(..., description="ID da pergunta vinculada ex: 'P01'")
    subdimensao: str = Field(..., description="Sub-dimensão vinculada")
    gatilho_score_max: int = Field(3, description="Score máximo para disparar a recomendação (<= 3)")
    acao_curto_prazo: str = Field(..., description="Ação imediata recomendada")
    acao_medio_prazo: str = Field(..., description="Ação estrutural de médio prazo")
    kpi_sugerido: str = Field(..., description="Métrica de sucesso predefinida")
    prioridade_padrao: str = Field("ALTA", description="Prioridade: 'ALTA', 'MEDIA' ou 'BAIXA'")


class CatalogoRecomendacoesRepository:
    """
    Repositório de acesso ao Catálogo de Recomendações alinhado à taxonomia de 37 perguntas.
    """
    @staticmethod
    async def buscar_recomendacoes_por_subdimensoes(scores_subdimensoes: Dict[str, float]) -> List[RecomendacaoCatalogoItem]:
        catalogo_mock: List[RecomendacaoCatalogoItem] = [
            RecomendacaoCatalogoItem(
                id_recomendacao=1,
                id_pergunta="P01",
                subdimensao="tecnologia.infraestrutura_cloud",
                gatilho_score_max=3,
                acao_curto_prazo="Realizar diagnóstico de demanda computacional (Sizing) para identificar picos de uso e definir capacidade em nuvem.",
                acao_medio_prazo="Configurar grupos de redimensionamento automático de recursos na nuvem para suporte dinâmico a IA.",
                kpi_sugerido="Porcentagem de instâncias de processamento com dimensionamento automático ativo",
                prioridade_padrao="ALTA"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao=7,
                id_pergunta="P07",
                subdimensao="organizacao.suporte_lideranca",
                gatilho_score_max=3,
                acao_curto_prazo="Realizar alinhamento executivo para vincular a adoção de IA às metas corporativas do ano.",
                acao_medio_prazo="Garantir uma reserva orçamentária dedicada no planejamento financeiro para projetos de inovação em dados e IA.",
                kpi_sugerido="Percentual do orçamento de TI alocado diretamente para iniciativas de IA",
                prioridade_padrao="ALTA"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao=11,
                id_pergunta="P11",
                subdimensao="organizacao.governanca_etica",
                gatilho_score_max=3,
                acao_curto_prazo="Elaborar uma política simples de uso responsável de IA cobrindo privacidade e LGPD.",
                acao_medio_prazo="Implementar uma etapa de validação ética e de mitigação de vieses antes de publicar novos algoritmos.",
                kpi_sugerido="100% dos projetos de IA aprovados em parecer de governança antes da entrada em produção",
                prioridade_padrao="ALTA"
            ),
            RecomendacaoCatalogoItem(
                id_recomendacao=13,
                id_pergunta="P13",
                subdimensao="dados.qualidade_saneamento",
                gatilho_score_max=3,
                acao_curto_prazo="Definir critérios claros de validação de dados (ausência de nulos, duplicidades e tipos corretos).",
                acao_medio_prazo="Automatizar etapas de verificação e limpeza de dados na entrada dos sistemas.",
                kpi_sugerido="Percentual de registros da base de dados em conformidade com as regras de qualidade (>= 95%)",
                prioridade_padrao="ALTA"
            )
        ]

        itens_selecionados: List[RecomendacaoCatalogoItem] = []
        for sub_key, score in scores_subdimensoes.items():
            if score <= 60.0:
                for item in catalogo_mock:
                    if item.subdimensao == sub_key:
                        itens_selecionados.append(item)

        return itens_selecionados


# ==============================================================================
# CONTRATOS E SCHEMAS DA API
# ==============================================================================
class HealthCheckOutput(BaseModel):
    status: str
    ollama_status: str
    modelo_ativo: str
    versao_api: str = "1.8.0"


class ModelInputPayload(BaseModel):
    empresa_nome: str = Field(..., description="Nome da organização avaliada", min_length=2)
    contexto_qualitativo: Optional[str] = Field(None, description="Observações textuais gerais")
    respostas: Dict[str, Dict[str, List[LikertScore]]] = Field(
        ..., description="Respostas objetivas organizadas por Dimensão e Sub-dimensão"
    )
    respostas_dissertativas: Optional[Dict[str, str]] = Field(default=None)


class ItemPlanoAcao(BaseModel):
    id_catalogo: int = Field(..., description="ID de referência no catálogo do banco de dados")
    fase: str = Field(..., description="Curto Prazo ou Médio Prazo")
    acao: str = Field(..., description="Ação recomendada extraída do catálogo")
    dimensao_foco: str = Field(..., description="Sub-dimensão tratada")
    prioridade: str = Field("ALTA", description="Prioridade: 'ALTA', 'MEDIA' ou 'BAIXA'")
    kpi_sucesso: Optional[str] = Field(None, description="Métrica de sucesso para a ação")


class RelatorioDiagnosticoLLM(BaseModel):
    diagnostico_geral: str = Field(..., description="Parecer executivo do estado de prontidão")
    resumo_executivo_clevel: str = Field(..., description="Síntese para a alta gestão")
    nivel_risco_implantacao: str = Field("Médio", description="Nível de risco")
    pontos_fortes: List[str] = Field(..., description="Pontos fortes identificados")
    gaps_criticos: List[str] = Field(..., description="Gargalos críticos")
    plano_de_acao: List[ItemPlanoAcao] = Field(..., description="Plano de ação ancorado no catálogo")


class ModelEvaluationOutput(BaseModel):
    score_geral: float = Field(..., description="Score global (0 a 100)")
    scores_dimensoes: Dict[str, float] = Field(..., description="Scores por dimensão principal")
    scores_subdimensoes: Dict[str, float] = Field(..., description="Scores por sub-dimensão")
    tempo_execucao_ms: float = Field(..., description="Tempo de processamento em ms")
    relatorio_llm: RelatorioDiagnosticoLLM


class SchemaDetalhadoOutput(BaseModel):
    pesos_dimensoes: Dict[str, float]
    subdimensoes_mapa: Dict[str, List[str]]
    total_perguntas: int = 37


# ==============================================================================
# ENGINE DETERMINÍSTICA DE CÁLCULO (PESO UNITÁRIO POR PERGUNTA)
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
    def processar_pontuacoes(cls, respostas: Dict[str, Dict[str, List[int]]]) -> Tuple[float, Dict[str, float], Dict[str, float]]:
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

            nota_dim_100 = round(sum(subdim_scores_lista) / len(subdim_scores_lista), 2) if subdim_scores_lista else 0.0
            scores_dimensoes[dim_key] = nota_dim_100
            
            peso_dim = PESOS_DIMENSOES.get(dim_key, 1.0 / len(SUBDIMENSOES_MAPA))
            score_ponderado_total += nota_dim_100 * peso_dim

        return round(score_ponderado_total, 2), scores_dimensoes, scores_subdimensoes


# ==============================================================================
# ORQUESTRADOR LLM COM ANCORAGEM
# ==============================================================================
class LLMOrchestrator:
    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "llama3.2")

    async def verificar_health(self, client: httpx.AsyncClient) -> bool:
        try:
            resp = await client.get(f"{self.base_url}/api/version", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def _construir_prompt(
        self,
        empresa: str,
        score: float,
        dim_scores: dict,
        recomendacoes_catalogo: List[RecomendacaoCatalogoItem]
    ) -> str:
        catalogo_json = [
            {
                "id_catalogo": item.id_recomendacao,
                "pergunta_ref": item.id_pergunta,
                "subdimensao": item.subdimensao,
                "curto_prazo": item.acao_curto_prazo,
                "medio_prazo": item.acao_medio_prazo,
                "kpi": item.kpi_sugerido,
                "prioridade": item.prioridade_padrao
            }
            for item in recomendacoes_catalogo
        ]

        return f"""Você é um auditor sênior em Prontidão Organizacional para Adoção de IA.
Selecione e estruture o plano de ação exclusivamente a partir do CATÁLOGO DO BANCO DE DADOS fornecido abaixo.

[DADOS DA EMPRESA]
- Empresa: {empresa}
- Score Geral: {score}/100
- Scores por Dimensão: {json.dumps(dim_scores, ensure_ascii=False)}

[CATÁLOGO DE RECOMENDAÇÕES DO BANCO]
{json.dumps(catalogo_json, ensure_ascii=False, indent=2)}

[REGRAS]
1. O plano de ação deve usar rigorosamente os dados do catálogo fornecido.
2. Responda estritamente em formato JSON válido compatível com o schema esperado."""

    async def gerar_diagnostico(
        self,
        client: httpx.AsyncClient,
        empresa_nome: str,
        score_geral: float,
        scores_dimensoes: dict,
        scores_subdimensoes: dict,
        recomendacoes_catalogo: List[RecomendacaoCatalogoItem]
    ) -> RelatorioDiagnosticoLLM:
        prompt = self._construir_prompt(empresa_nome, score_geral, scores_dimensoes, recomendacoes_catalogo)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "format": RelatorioDiagnosticoLLM.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                return RelatorioDiagnosticoLLM(**json.loads(data.get("response", "{}")))
            else:
                return self._gerar_fallback(score_geral, recomendacoes_catalogo)
        except Exception:
            return self._gerar_fallback(score_geral, recomendacoes_catalogo)

    def _gerar_fallback(self, score_geral: float, recomendacoes_catalogo: List[RecomendacaoCatalogoItem]) -> RelatorioDiagnosticoLLM:
        plano = [
            ItemPlanoAcao(
                id_catalogo=item.id_recomendacao,
                fase="Curto Prazo",
                acao=item.acao_curto_prazo,
                dimensao_foco=item.subdimensao,
                prioridade=item.prioridade_padrao,
                kpi_sucesso=item.kpi_sugerido
            )
            for item in recomendacoes_catalogo[:3]
        ]
        return RelatorioDiagnosticoLLM(
            diagnostico_geral=f"Diagnóstico automatizado (Fallback): Score global de {score_geral}/100.",
            resumo_executivo_clevel="Priorizar mitigação dos gargalos mapeados no catálogo.",
            nivel_risco_implantacao="Alto" if score_geral < 50 else "Médio",
            pontos_fortes=["Cálculo determinístico executado com sucesso."],
            gaps_criticos=["Gargalos identificados vinculados ao catálogo relacional."],
            plano_de_acao=plano
        )


# ==============================================================================
# ROTAS FASTAPI
# ==============================================================================
http_client: Optional[httpx.AsyncClient] = None
llm_orchestrator = LLMOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=35.0)
    yield
    await http_client.aclose()

app = FastAPI(title="AI Readiness Model Service", version="1.8.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/model/schema", response_model=SchemaDetalhadoOutput)
async def obter_schema_modelo():
    return SchemaDetalhadoOutput(
        pesos_dimensoes=PESOS_DIMENSOES,
        subdimensoes_mapa=SUBDIMENSOES_MAPA,
        total_perguntas=37
    )

@app.post("/api/v1/model/evaluate", response_model=ModelEvaluationOutput)
async def executar_avaliacao_modelo(
    payload: ModelInputPayload,
    dry_run: bool = Query(False, description="Se True, executa cálculo simulado sem chamar o LLM.")
):
    inicio_tempo = time.perf_counter()
    
    erro_taxonomia = ScoreEngine.validar_taxonomia_payload(payload.respostas)
    if erro_taxonomia:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=erro_taxonomia)

    score_geral, scores_dimensoes, scores_subdimensoes = ScoreEngine.processar_pontuacoes(payload.respostas)
    recomendacoes_catalogo = await CatalogoRecomendacoesRepository.buscar_recomendacoes_por_subdimensoes(scores_subdimensoes)

    if dry_run:
        relatorio_llm = llm_orchestrator._gerar_fallback(score_geral, recomendacoes_catalogo)
    else:
        relatorio_llm = await llm_orchestrator.gerar_diagnostico(
            http_client, payload.empresa_nome, score_geral, scores_dimensoes, scores_subdimensoes, recomendacoes_catalogo
        )

    tempo_ms = round((time.perf_counter() - inicio_tempo) * 1000.0, 2)

    return ModelEvaluationOutput(
        score_geral=score_geral,
        scores_dimensoes=scores_dimensoes,
        scores_subdimensoes=scores_subdimensoes,
        tempo_execucao_ms=tempo_ms,
        relatorio_llm=relatorio_llm
    )