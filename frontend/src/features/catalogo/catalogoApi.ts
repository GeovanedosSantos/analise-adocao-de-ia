import { requisicao } from '@/api/cliente'

export type Prazo = 'CURTO' | 'MEDIO' | 'LONGO'

/** Escala de prioridade, esforço e impacto. */
export type Nivel = 'ALTO' | 'MEDIO' | 'BAIXO'

export type Recomendacao = {
  id: string
  codigo: string
  dimensao_codigo: string
  /** Nome na versão ativa do questionário; o código, se a dimensão não existir nela. */
  dimensao_nome: string
  titulo: string
  descricao: string
  /** Faixa da nota da dimensão em que a recomendação vale: [nota_minima, nota_maxima). */
  nota_minima: number
  nota_maxima: number
  prazo: Prazo
  prioridade: Nivel
  esforco: Nivel
  impacto: Nivel
  kpi: string
}

export const ROTULO_PRAZO: Record<Prazo, string> = {
  CURTO: 'Curto prazo · 0 a 3 meses',
  MEDIO: 'Médio prazo · 3 a 6 meses',
  LONGO: 'Longo prazo · 6 a 12+ meses',
}

export const ROTULO_NIVEL: Record<Nivel, string> = { ALTO: 'Alto', MEDIO: 'Médio', BAIXO: 'Baixo' }

/** Prioridade é feminino: "Prioridade: Alta". */
export const ROTULO_PRIORIDADE: Record<Nivel, string> = { ALTO: 'Alta', MEDIO: 'Média', BAIXO: 'Baixa' }

/** Recomendações ativas do catálogo, por dimensão e faixa de nota. */
export async function listarCatalogo() {
  return (await requisicao<Recomendacao[]>('/recomendacoes/')).dados
}
