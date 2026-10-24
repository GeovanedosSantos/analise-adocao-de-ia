import type { ButtonHTMLAttributes } from 'react'

type Variante = 'primario' | 'secundario' | 'link'

const FOCO = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-destaque'

const ESTILOS: Record<Variante, string> = {
  primario: `rounded bg-destaque px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 ${FOCO}`,
  secundario: `rounded border border-borda px-4 py-2 font-medium text-titulo disabled:cursor-not-allowed disabled:opacity-60 ${FOCO}`,
  link: `rounded-sm font-medium text-destaque underline underline-offset-2 disabled:opacity-60 ${FOCO}`,
}

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante }

/**
 * Botão padrão do app. `className` serve para posicionar (ex.: `self-start`), não para
 * mudar cor ou espaçamento: para isso, use ou crie uma variante.
 */
export function Botao({ variante = 'primario', type = 'button', className = '', ...props }: Props) {
  return <button type={type} className={`${ESTILOS[variante]} ${className}`} {...props} />
}
