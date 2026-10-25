import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router'
import { tv, type VariantProps } from 'tailwind-variants'

const botao = tv({
  // inline-flex alinha ícone e texto quando o botão tem um ícone do lucide-react
  // Pressionar encolhe 3% (só transform, roda na GPU); desabilitado não reage
  base: 'inline-flex touch-manipulation items-center justify-center gap-2 text-sm font-medium transition-[transform,background-color] duration-150 ease-saida focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-destaque enabled:active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60',
  variants: {
    variante: {
      primario: 'h-10 rounded-lg bg-destaque px-4 text-sobre-destaque shadow-sm hover:bg-destaque/90',
      secundario: 'h-10 rounded-lg border border-borda bg-superficie px-4 text-titulo shadow-xs hover:bg-suave',
      link: 'rounded-sm text-destaque underline-offset-4 hover:underline active:scale-100',
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
