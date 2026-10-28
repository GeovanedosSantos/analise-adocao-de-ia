import type { ItemRascunho } from './rascunho/agendador'
import { baixarArquivo, requisicao } from '@/api/cliente'
import type { Recomendacao } from '@/features/catalogo/catalogoApi'

export type TipoPergunta = 'OBJETIVA' | 'DISSERTATIVA'

/** `fator`: nome do fator de prontidão que a pergunta mede, se houver. */
export type Pergunta = { id: string; texto: string; tipo: TipoPergunta; ordem: number; fator: string | null }

export type Dimensao = { id: string; codigo: string; nome: string; descricao: string; ordem: number; perguntas: Pergunta[] }

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
  dimensao_peso: number
  /** Fatores de prontidão medidos na dimensão. */
  fatores: string[]
  nota: number
  prioritaria: boolean
  /** Nota da mesma dimensão na avaliação anterior; null se não houver anterior. */
  nota_anterior: number | null
  /** Variação percentual em relação à nota anterior; null sem anterior ou com anterior 0. */
  delta_percentual: number | null
}

/** Item do plano de ação: uma recomendação do catálogo, na posição em que foi priorizada. */
export type ItemPlano = Omit<Recomendacao, 'id' | 'dimensao_nome' | 'nota_minima' | 'nota_maxima'> & {
  posicao: number
  nota_dimensao: number
}

export type Avaliacao = {
  id: string
  status: StatusAvaliacao
  questionario: string
  versao_questionario: string
  data_inicio: string
  data_fim: string | null
  nota_geral: number | null
  /** De 1 a 5. */
  nivel_prontidao: number | null
  /** Índice geral da avaliação anterior; null na primeira. */
  nota_geral_anterior: number | null
  /** Variação percentual do índice geral; null na primeira ou com anterior 0. */
  delta_nota_geral: number | null
  respostas: Resposta[]
  pontuacoes: Pontuacao[]
  /** Até 10 recomendações do catálogo, da mais importante para a menos importante. */
  recomendacoes: ItemPlano[]
  /** A IA já ordenou o plano; enquanto false, vale a ordem do catálogo. */
  recomendacoes_ordenadas_ia: boolean
}

/** Como vem na listagem: sem respostas, pontuações nem plano de ação. */
export type AvaliacaoResumo = Omit<
  Avaliacao,
  'questionario' | 'respostas' | 'pontuacoes' | 'recomendacoes' | 'recomendacoes_ordenadas_ia'
>

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

/** Recomeça o rascunho: apaga as respostas já dadas (UC02 FA02). */
export async function descartarRascunho(avaliacaoId: string) {
  await requisicao(`/avaliacoes/${avaliacaoId}/descartar/`, { metodo: 'POST' })
}

/** 202: a IA ainda analisa as respostas abertas; 200: resultado pronto. */
export async function submeterAvaliacao(avaliacaoId: string) {
  return (await requisicao<Avaliacao>(`/avaliacoes/${avaliacaoId}/submeter/`, { metodo: 'POST' })).dados
}

export async function consultarStatus(avaliacaoId: string) {
  return (await requisicao<{ id: string; status: StatusAvaliacao }>(`/avaliacoes/${avaliacaoId}/status/`)).dados
}

/** Relatório em PDF. 503: a geração falhou ou passou do tempo (detalhe no ErroApi). */
export async function baixarPdf(avaliacaoId: string) {
  await baixarArquivo(`/avaliacoes/${avaliacaoId}/pdf/`, 'avaliacao-prontidao-ia.pdf')
}
