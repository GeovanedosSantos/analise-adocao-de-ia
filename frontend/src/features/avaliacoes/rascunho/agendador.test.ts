import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { criarAgendadorRascunho, type ItemRascunho } from './agendador'

describe('agendador de rascunho', () => {
  let enviados: ItemRascunho[][]
  let salvar: (itens: ItemRascunho[]) => Promise<void>

  beforeEach(() => {
    vi.useFakeTimers()
    enviados = []
    salvar = vi.fn(async (itens: ItemRascunho[]) => {
      enviados.push(itens)
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('espera a pausa na digitação e envia só a última edição de cada pergunta', async () => {
    const agendador = criarAgendadorRascunho(salvar, { atrasoMs: 800 })

    agendador.registrar({ pergunta: 'p1', valor_objetivo: 2 })
    agendador.registrar({ pergunta: 'p1', valor_objetivo: 4 })
    agendador.registrar({ pergunta: 'p2', texto_aberto: 'Temos dados' })
    await vi.advanceTimersByTimeAsync(799)
    expect(enviados).toEqual([])

    await vi.advanceTimersByTimeAsync(1)
    expect(enviados).toEqual([
      [
        { pergunta: 'p1', valor_objetivo: 4 },
        { pergunta: 'p2', texto_aberto: 'Temos dados' },
      ],
    ])
  })

  it('em caso de falha mantém as respostas e tenta de novo', async () => {
    const estados: string[] = []
    let falhar = true
    salvar = vi.fn(async (itens: ItemRascunho[]) => {
      if (falhar) throw new Error('rede')
      enviados.push(itens)
    })
    const agendador = criarAgendadorRascunho(salvar, {
      atrasoMs: 800,
      atrasoRetentativaMs: 5000,
      aoMudarEstado: (estado) => estados.push(estado),
    })

    agendador.registrar({ pergunta: 'p1', valor_objetivo: 3 })
    await vi.advanceTimersByTimeAsync(800)
    expect(agendador.temPendentes()).toBe(true)

    falhar = false
    await vi.advanceTimersByTimeAsync(5000)
    expect(enviados).toEqual([[{ pergunta: 'p1', valor_objetivo: 3 }]])
    expect(estados).toEqual(['salvando', 'erro', 'salvando', 'salvo'])
  })

  it('edição feita durante um envio que falhou não é sobrescrita pelo valor antigo', async () => {
    let rejeitar: (erro: Error) => void = () => {}
    salvar = vi.fn(() => new Promise<void>((_, reject) => (rejeitar = reject)))
    const agendador = criarAgendadorRascunho(salvar, { atrasoMs: 800 })

    agendador.registrar({ pergunta: 'p1', valor_objetivo: 1 })
    await vi.advanceTimersByTimeAsync(800)
    agendador.registrar({ pergunta: 'p1', valor_objetivo: 5 })
    rejeitar(new Error('rede'))
    await vi.advanceTimersByTimeAsync(0)

    salvar = vi.fn()
    expect(agendador.pendentes()).toEqual([{ pergunta: 'p1', valor_objetivo: 5 }])
  })

  it('descarregar envia na hora, sem esperar o atraso', async () => {
    const agendador = criarAgendadorRascunho(salvar, { atrasoMs: 800 })
    agendador.registrar({ pergunta: 'p1', valor_objetivo: 3 })

    await agendador.descarregar()

    expect(enviados).toEqual([[{ pergunta: 'p1', valor_objetivo: 3 }]])
  })
})
