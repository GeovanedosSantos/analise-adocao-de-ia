import type { ReactNode } from 'react'

type Tipo = 'info' | 'aviso' | 'erro'

const ESTILOS: Record<Tipo, string> = {
  info: 'border-destaque/40 bg-destaque-fundo',
  aviso: 'border-amber-400/60 bg-amber-50 dark:border-amber-500/40 dark:bg-amber-950/40',
  erro: 'border-red-400/60 bg-red-50 dark:border-red-500/40 dark:bg-red-950/40',
}

type Props = {
  tipo?: Tipo
  titulo?: string
  /** Botão ou link para resolver a situação (ex.: "Verificar de novo"). */
  acao?: ReactNode
  children: ReactNode
}

/** Mensagem em destaque na página. Erros são anunciados na hora por leitores de tela; o resto, sem interromper. */
export function Alerta({ tipo = 'info', titulo, acao, children }: Props) {
  return (
    <div
      role={tipo === 'erro' ? 'alert' : 'status'}
      className={`flex flex-col items-start gap-3 rounded border px-4 py-3 text-sm text-titulo ${ESTILOS[tipo]}`}
    >
      <div className="flex flex-col gap-1">
        {titulo && <p className="font-medium">{titulo}</p>}
        <div>{children}</div>
      </div>
      {acao}
    </div>
  )
}
