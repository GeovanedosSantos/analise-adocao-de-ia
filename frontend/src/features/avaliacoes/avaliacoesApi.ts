import type { ItemRascunho } from './rascunho/agendador'
import { requisicao } from '@/api/cliente'

export type TipoPergunta = 'OBJETIVA' | 'DISSERTATIVA'

export type Pergunta = { id: string; texto: string; tipo: TipoPergunta; ordem: number }

export type Dimensao = { id: string; nome: string; ordem: number; perguntas: Pergunta[] }

export type Questionario = { id: string; versao: string; descricao: string; dimensoes: Dimensao[] }

export type StatusAvaliacao = 'DRAFT' | 'PROCESSANDO_IA' | 'ERRO_PROCESSAMENTO' | 'CONCLUIDA'

export type Resposta = {
  pergunta: string
  valor_objetivo: number | null
  texto_aberto: string
  feedback_ia: { analise_qualitativa: string; pontos_fortes: string[]; riscos: string[] } | null
}

export type Pontuacao = {
  dimensao: string
  dimensao_codigo: string
  dimensao_nome: string
  nota: number
  prioritaria: boolean
  /** Diferença em pontos para a mesma dimensão na avaliação anterior; null se não houver anterior. */
  delta_percentual: number | null
}

export type Avaliacao = {
  id: string
  status: StatusAvaliacao
  questionario: string
  versao_questionario: string
  data_inicio: string
  data_fim: string | null
  nota_geral: number | null
  nivel_maturidade: number | null
  apta: boolean | null
  /** Diferença em pontos para a nota geral da avaliação anterior; null na primeira. */
  delta_nota_geral: number | null
  respostas: Resposta[]
  pontuacoes: Pontuacao[]
}

/** Como vem na listagem: sem respostas nem pontuações. */
export type AvaliacaoResumo = Omit<Avaliacao, 'questionario' | 'respostas' | 'pontuacoes'>

/** Resumo com pontuações por dimensão, usado pelo dashboard e histórico. */
export type AvaliacaoHistorico = AvaliacaoResumo & { pontuacoes: Pontuacao[] }

/** Avaliações da empresa, da mais recente para a mais antiga (inclui o rascunho, se houver). */
export async function listarAvaliacoes() {
  return (await requisicao<AvaliacaoResumo[]>('/avaliacoes/')).dados
}

/** Histórico da empresa com pontuações por dimensão, sem carregar respostas. */
export async function obterHistorico() {
  return (await requisicao<AvaliacaoHistorico[]>('/avaliacoes/historico/')).dados
}

/** Retoma o rascunho da empresa ou abre um novo na versão ativa. */
export async function iniciarAvaliacao() {
  return (await requisicao<Avaliacao>('/avaliacoes/', { metodo: 'POST' })).dados
}

export async function obterAvaliacao(id: string) {
  return (await requisicao<Avaliacao>(`/avaliacoes/${id}/`)).dados
}

export async function obterQuestionario(id: string) {
  return (await requisicao<Questionario>(`/questionarios/${id}/`)).dados
}

export async function salvarRascunho(avaliacaoId: string, respostas: ItemRascunho[]) {
  await requisicao(`/avaliacoes/${avaliacaoId}/rascunho/`, { metodo: 'PATCH', corpo: { respostas } })
}

/** 202: a IA ainda analisa as respostas abertas; 200: resultado pronto. */
export async function submeterAvaliacao(avaliacaoId: string) {
  return (await requisicao<Avaliacao>(`/avaliacoes/${avaliacaoId}/submeter/`, { metodo: 'POST' })).dados
}

export async function consultarStatus(avaliacaoId: string) {
  return (await requisicao<{ id: string; status: StatusAvaliacao }>(`/avaliacoes/${avaliacaoId}/status/`)).dados
}
