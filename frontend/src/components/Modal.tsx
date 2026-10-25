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
      // Entra com fade + leve aumento (de 0,96, nunca de 0); só opacity e transform, 200 ms ease-out
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-xl border border-borda bg-superficie p-6 text-texto shadow-xl transition-[opacity,scale,display,overlay] transition-discrete duration-200 ease-saida backdrop:bg-black/50 not-open:scale-96 not-open:opacity-0 starting:open:scale-96 starting:open:opacity-0"
    >
      <div className="flex flex-col gap-4">
        <h2 id={idTitulo}>{titulo}</h2>
        {children}
        <div className="flex flex-wrap justify-end gap-3">{acoes}</div>
      </div>
    </dialog>
  )
}
