import { useEffect, useState } from 'react'
import { salvarRascunho } from '../avaliacoesApi'
import { criarAgendadorRascunho, type EstadoRascunho } from './agendador'

/** Liga o agendador de rascunho ao ciclo de vida do formulário. */
export function useRascunho(avaliacaoId: string) {
  const [estado, setEstado] = useState<EstadoRascunho | null>(null)
  const [agendador] = useState(() =>
    criarAgendadorRascunho((itens) => salvarRascunho(avaliacaoId, itens), { aoMudarEstado: setEstado }),
  )

  useEffect(() => {
    const avisarPendencias = (evento: BeforeUnloadEvent) => {
      if (agendador.temPendentes()) evento.preventDefault()
    }
    window.addEventListener('beforeunload', avisarPendencias)
    return () => {
      window.removeEventListener('beforeunload', avisarPendencias)
      agendador.cancelar()
    }
  }, [agendador])

  return { agendador, estado }
}
