import { useEffect, useId, useRef, type ReactNode } from 'react'

type Props = {
  aberto: boolean
  titulo: string
  /** Chamado quando a pessoa fecha com Esc. Quem abre o modal decide se ele fecha. */
  aoFechar: () => void
  acoes: ReactNode
  children: ReactNode
}

/** Diálogo modal sobre a página, com o `<dialog>` nativo: foco preso no modal e Esc para fechar. */
export function Modal({ aberto, titulo, aoFechar, acoes, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const idTitulo = useId()

  useEffect(() => {
    const dialogo = ref.current
    if (!dialogo) return
    if (aberto && !dialogo.open) dialogo.showModal()
    if (!aberto && dialogo.open) dialogo.close()
  }, [aberto])

  return (
    <dialog
      ref={ref}
      aria-labelledby={idTitulo}
      onCancel={(evento) => {
        // O Esc fecharia o diálogo por conta própria; quem controla o estado é o componente pai
        evento.preventDefault()
        aoFechar()
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-lg border border-borda bg-fundo p-6 text-texto shadow-xl backdrop:bg-black/50"
    >
      <div className="flex flex-col gap-4">
        <h2 id={idTitulo}>{titulo}</h2>
        {children}
        <div className="flex flex-wrap justify-end gap-3">{acoes}</div>
      </div>
    </dialog>
  )
}
