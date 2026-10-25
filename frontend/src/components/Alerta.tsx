import type { ReactNode } from 'react'
import { tv, type VariantProps } from 'tailwind-variants'

const alerta = tv({
  base: 'flex flex-col items-start gap-3 rounded border px-4 py-3 text-sm text-titulo',
  variants: {
    tipo: {
      info: 'border-destaque/40 bg-destaque-fundo',
      sucesso: 'border-green-500/50 bg-green-50 dark:border-green-500/40 dark:bg-green-950/40',
      aviso: 'border-amber-400/60 bg-amber-50 dark:border-amber-500/40 dark:bg-amber-950/40',
      erro: 'border-red-400/60 bg-red-50 dark:border-red-500/40 dark:bg-red-950/40',
    },
  },
  defaultVariants: { tipo: 'info' },
})

type Props = VariantProps<typeof alerta> & {
  titulo?: string
  /** Botão ou link para resolver a situação (ex.: "Verificar de novo"). */
  acao?: ReactNode
  children: ReactNode
}

/** Mensagem em destaque na página. Erros são anunciados na hora por leitores de tela; o resto, sem interromper. */
export function Alerta({ tipo = 'info', titulo, acao, children }: Props) {
  return (
    <div role={tipo === 'erro' ? 'alert' : 'status'} className={alerta({ tipo })}>
      <div className="flex flex-col gap-1">
        {titulo && <p className="font-medium">{titulo}</p>}
        <div>{children}</div>
      </div>
      {acao}
    </div>
  )
}
