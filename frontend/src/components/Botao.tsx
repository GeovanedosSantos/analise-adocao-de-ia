import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router'
import { tv, type VariantProps } from 'tailwind-variants'

const botao = tv({
  // inline-flex alinha ícone e texto quando o botão tem um ícone do lucide-react
  base: 'inline-flex items-center justify-center gap-2 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-destaque disabled:cursor-not-allowed disabled:opacity-60',
  variants: {
    variante: {
      primario: 'rounded bg-destaque px-4 py-2 text-sobre-destaque',
      secundario: 'rounded border border-borda px-4 py-2 text-titulo',
      link: 'rounded-sm text-destaque underline underline-offset-2',
    },
  },
  defaultVariants: { variante: 'primario' },
})

type Props = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof botao>

/**
 * Botão padrão do app. Classes passadas em `className` sobrescrevem as da variante
 * (o tailwind-merge resolve o conflito), mas um estilo que se repete deve virar variante.
 */
export function Botao({ variante, type = 'button', className, ...props }: Props) {
  return <button type={type} className={botao({ variante, className })} {...props} />
}

type PropsLink = LinkProps & VariantProps<typeof botao>

/** Link com aparência de botão, para ações que levam a outra página (ex.: "Responder questionário"). */
export function BotaoLink({ variante, className, ...props }: PropsLink) {
  return <Link className={botao({ variante, className })} {...props} />
}
