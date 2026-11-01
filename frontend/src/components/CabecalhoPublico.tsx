import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { AlternarTema } from './AlternarTema'
import { NomeProduto, SimboloLogo } from './Logo'

/**
 * Cabeçalho das páginas sem login (apresentação, entrar, cadastro, senha).
 * A logo leva à apresentação; `acoes` fica à direita, depois do botão de tema.
 */
export function CabecalhoPublico({ acoes }: { acoes?: ReactNode }) {
  return (
    <header className="flex items-center justify-between gap-3 px-4 py-4 sm:px-10 sm:py-5">
      <Link
        to="/"
        aria-label="Adoção de IA, ir para a apresentação"
        className="flex min-w-0 items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-destaque"
      >
        <SimboloLogo />
        {/* Em telas muito estreitas fica só o símbolo, para os botões de entrar e criar conta caberem */}
        <NomeProduto className="hidden min-[400px]:inline" />
      </Link>
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <AlternarTema />
        {acoes}
      </div>
    </header>
  )
}
