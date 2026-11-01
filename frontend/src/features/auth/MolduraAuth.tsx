import type { ReactNode } from 'react'
import { CabecalhoPublico } from '@/components/CabecalhoPublico'

/** Duas manchas de luz fixas (gradientes, sem imagem), as mesmas do login e da apresentação. */
export function FundoLuzes() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-1/3 -left-1/4 size-[60rem] rounded-full bg-[radial-gradient(circle,rgba(65,105,225,0.14),transparent_60%)] dark:bg-[radial-gradient(circle,rgba(65,105,225,0.22),transparent_60%)]" />
      <div className="absolute -right-1/4 -bottom-1/3 size-[56rem] rounded-full bg-[radial-gradient(circle,rgba(124,92,230,0.10),transparent_60%)] dark:bg-[radial-gradient(circle,rgba(124,92,230,0.16),transparent_60%)]" />
    </div>
  )
}

/** Cartão do formulário, com o vidro fosco do login. */
export const CLASSE_CARTAO_AUTH =
  'flex flex-col gap-4 rounded-2xl border border-borda bg-superficie/85 p-6 shadow-xl shadow-slate-900/5 backdrop-blur-md dark:shadow-black/40'

type Props = {
  titulo: string
  descricao?: ReactNode
  /** Botões no canto direito do cabeçalho (ex.: "Entrar" na tela de cadastro). */
  acoesCabecalho?: ReactNode
  /** Links abaixo do cartão (ex.: "Já tem conta? Entrar"). */
  rodape?: ReactNode
  largura?: 'estreita' | 'media'
  children: ReactNode
}

/** Moldura das telas de conta: cadastro, retorno do Google e recuperação de senha. */
export function MolduraAuth({ titulo, descricao, acoesCabecalho, rodape, largura = 'estreita', children }: Props) {
  return (
    <main className="relative isolate flex flex-1 flex-col bg-fundo">
      <FundoLuzes />
      <CabecalhoPublico acoes={acoesCabecalho} />
      <div className="flex flex-1 items-start justify-center px-4 pt-4 pb-16 sm:items-center sm:px-6 sm:pt-0">
        <div
          className={`flex w-full flex-col gap-4 transition-[opacity,translate] duration-300 ease-saida starting:opacity-0 motion-safe:starting:translate-y-2 ${largura === 'media' ? 'max-w-lg' : 'max-w-sm'}`}
        >
          <div className={CLASSE_CARTAO_AUTH}>
            <div className="flex flex-col gap-1">
              <h1 className="text-xl">{titulo}</h1>
              {descricao && <p className="text-sm">{descricao}</p>}
            </div>
            {children}
          </div>
          {rodape && <div className="text-center text-sm">{rodape}</div>}
        </div>
      </div>
    </main>
  )
}
