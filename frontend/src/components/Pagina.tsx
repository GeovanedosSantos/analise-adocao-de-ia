import type { ReactNode } from 'react'
import { Alerta } from './Alerta'

type Props = {
  titulo: string
  descricao?: ReactNode
  /** Botões ou links no canto do cabeçalho da página. */
  acoes?: ReactNode
  children: ReactNode
}

/** Moldura das páginas logadas: título, descrição e conteúdo com largura máxima. */
export function Pagina({ titulo, descricao, acoes, children }: Props) {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1>{titulo}</h1>
          {descricao && <p className="text-sm">{descricao}</p>}
        </div>
        {acoes && <div className="flex flex-wrap gap-2">{acoes}</div>}
      </header>
      {children}
    </div>
  )
}

type PropsCartao = { titulo?: string; descricao?: string; acao?: ReactNode; className?: string; children: ReactNode }

/** Bloco de conteúdo com borda; o título é opcional para cartões que só agrupam. */
export function Cartao({ titulo, descricao, acao, className = '', children }: PropsCartao) {
  return (
    <section className={`cartao flex min-w-0 flex-col gap-4 p-5 sm:p-6 ${className}`}>
      {(titulo || acao) && (
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-0.5">
            {titulo && <h2>{titulo}</h2>}
            {descricao && <p className="text-sm">{descricao}</p>}
          </div>
          {acao}
        </div>
      )}
      {children}
    </section>
  )
}

/** Mensagem sozinha na página (erro, vazio), com o mesmo recuo das páginas. */
export function MensagemPagina(props: Parameters<typeof Alerta>[0]) {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <Alerta {...props} />
    </div>
  )
}

/** Enquanto a página busca os dados. */
export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return (
    <p role="status" className="mx-auto w-full max-w-7xl px-4 py-6 text-sm sm:px-6 lg:px-8 lg:py-8">
      {texto}
    </p>
  )
}
