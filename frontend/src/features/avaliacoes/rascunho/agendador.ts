export type ItemRascunho = {
  pergunta: string
  valor_objetivo?: number | null
  texto_aberto?: string
}

export type EstadoRascunho = 'salvando' | 'salvo' | 'erro'

type Opcoes = {
  atrasoMs?: number
  atrasoRetentativaMs?: number
  aoMudarEstado?: (estado: EstadoRascunho) => void
}

/**
 * Salva o rascunho em segundo plano (RF04): junta as edições, envia após uma pausa na
 * digitação e, se o envio falhar, guarda as respostas e tenta de novo.
 */
export function criarAgendadorRascunho(
  salvar: (itens: ItemRascunho[]) => Promise<void>,
  { atrasoMs = 800, atrasoRetentativaMs = 5000, aoMudarEstado }: Opcoes = {},
) {
  const pendentes = new Map<string, ItemRascunho>()
  let timer: ReturnType<typeof setTimeout> | undefined

  function agendar(atraso: number) {
    clearTimeout(timer)
    timer = setTimeout(() => void descarregar().catch(() => {}), atraso)
  }

  function registrar(item: ItemRascunho) {
    pendentes.set(item.pergunta, item)
    agendar(atrasoMs)
  }

  async function descarregar() {
    clearTimeout(timer)
    if (pendentes.size === 0) return
    const lote = [...pendentes.values()]
    pendentes.clear()
    aoMudarEstado?.('salvando')
    try {
      await salvar(lote)
      aoMudarEstado?.('salvo')
    } catch (erro) {
      // Devolve à fila só o que não foi editado de novo enquanto o envio acontecia
      for (const item of lote) {
        if (!pendentes.has(item.pergunta)) pendentes.set(item.pergunta, item)
      }
      aoMudarEstado?.('erro')
      agendar(atrasoRetentativaMs)
      throw erro
    }
  }

  return {
    registrar,
    descarregar,
    pendentes: () => [...pendentes.values()],
    temPendentes: () => pendentes.size > 0,
    cancelar: () => clearTimeout(timer),
  }
}
