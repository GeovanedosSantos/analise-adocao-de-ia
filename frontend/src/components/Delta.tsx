import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react'
import { tv } from 'tailwind-variants'

const delta = tv({
  base: 'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-xs font-semibold whitespace-nowrap tabular-nums',
  variants: {
    sentido: {
      subiu: 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-400',
      caiu: 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-400',
      igual: 'bg-suave text-texto',
    },
  },
})

const formato = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1, signDisplay: 'exceptZero' })

type Props = {
  valor: number | null | undefined
  /** Com o que a diferença é calculada, para o title e leitores de tela. */
  referencia?: string
}

/** Variação percentual em relação à avaliação anterior (RF12). Sem variação (null), não mostra nada. */
export function Delta({ valor, referencia = 'à avaliação anterior' }: Props) {
  if (valor == null) return null
  // Arredonda antes de comparar: 0,04 aparece como "0,0" e não deve vir com seta para cima
  const arredondado = Math.round(valor * 10) / 10
  const sentido = arredondado > 0 ? 'subiu' : arredondado < 0 ? 'caiu' : 'igual'
  const Icone = { subiu: ArrowUpRight, caiu: ArrowDownRight, igual: ArrowRight }[sentido]
  return (
    <span className={delta({ sentido })} title={`Em relação ${referencia}`}>
      <Icone aria-hidden size={13} strokeWidth={2.5} />
      {formato.format(arredondado)}%
      <span className="sr-only"> em relação {referencia}</span>
    </span>
  )
}
