import type { ReactNode } from 'react'

type Props = {
  rotulo: string
  valor: string
  /** Normalmente um <Delta />, ao lado do valor. */
  variacao?: ReactNode
  /** Linha pequena abaixo do valor (ex.: "vs avaliação anterior"). */
  rodape?: string
  /** Valores em ordem cronológica para o mini gráfico; com menos de 2, não desenha. */
  serie?: number[]
}

/** Cartão de indicador (KPI): rótulo, valor em destaque, variação e mini gráfico opcional. */
export function Indicador({ rotulo, valor, variacao, rodape, serie }: Props) {
  return (
    <div className="cartao flex min-w-0 flex-col gap-1 p-4">
      <dt className="text-sm">{rotulo}</dt>
      <dd className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-2xl font-semibold tracking-tight text-titulo tabular-nums [overflow-wrap:anywhere]">{valor}</span>
        {variacao}
      </dd>
      {rodape && <dd className="text-xs">{rodape}</dd>}
      {serie && serie.length >= 2 && (
        <dd className="mt-2">
          <MiniGrafico valores={serie} />
        </dd>
      )}
    </div>
  )
}

const LARGURA = 120
const ALTURA = 32

/** Sparkline em SVG puro (sem biblioteca). Escala na faixa dos próprios valores: mostra a tendência, não o nível. */
function MiniGrafico({ valores }: { valores: number[] }) {
  const min = Math.min(...valores)
  // Faixa mínima de 10 pontos: variações pequenas não viram um zigue-zague exagerado
  const faixa = Math.max(Math.max(...valores) - min, 10)
  const pontos = valores.map((v, i) => [(i / (valores.length - 1)) * LARGURA, ALTURA - 2 - ((v - min) / faixa) * (ALTURA - 4)])
  const linha = pontos.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join('')
  return (
    // Decorativo: os valores aparecem no gráfico grande e no histórico. Estica na largura do cartão
    <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} className="h-8 w-full overflow-visible" preserveAspectRatio="none" aria-hidden>
      <path d={`${linha}L${LARGURA},${ALTURA}L0,${ALTURA}Z`} fill="var(--serie-atual)" opacity={0.12} />
      <path d={linha} fill="none" stroke="var(--serie-atual)" strokeWidth={2} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  )
}
