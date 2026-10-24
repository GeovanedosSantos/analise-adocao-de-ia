import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { acompanharProcessamento } from './acompanhamento'

describe('acompanhamento do processamento', () => {
  let eventos: { aoTerminar: ReturnType<typeof vi.fn>; aoEsgotar: ReturnType<typeof vi.fn>; aoFalhar: ReturnType<typeof vi.fn> }

  beforeEach(() => {
    vi.useFakeTimers()
    eventos = { aoTerminar: vi.fn(), aoEsgotar: vi.fn(), aoFalhar: vi.fn() }
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('para de consultar quando o processamento termina', async () => {
    const consultar = vi.fn().mockResolvedValueOnce(null).mockResolvedValueOnce('CONCLUIDA')
    acompanharProcessamento(consultar, eventos, { intervaloInicialMs: 1000, fator: 1 })

    await vi.advanceTimersByTimeAsync(2000)
    await vi.advanceTimersByTimeAsync(10_000)

    expect(consultar).toHaveBeenCalledTimes(2)
    expect(eventos.aoTerminar).toHaveBeenCalledWith('CONCLUIDA')
    expect(eventos.aoEsgotar).not.toHaveBeenCalled()
  })

  it('espaça as consultas até o intervalo máximo', async () => {
    const consultar = vi.fn().mockResolvedValue(null)
    acompanharProcessamento(consultar, eventos, { intervaloInicialMs: 1000, fator: 2, intervaloMaximoMs: 4000 })

    // Esperas: 1s, 2s, 4s, 4s → consultas em 1s, 3s, 7s e 11s
    let agora = 0
    for (const [instante, consultas] of [[999, 0], [1000, 1], [2999, 1], [3000, 2], [7000, 3], [10_999, 3], [11_000, 4]]) {
      await vi.advanceTimersByTimeAsync(instante - agora)
      agora = instante
      expect(consultar).toHaveBeenCalledTimes(consultas)
    }
  })

  it('desiste no limite de tempo e avisa a tela', async () => {
    const consultar = vi.fn().mockResolvedValue(null)
    acompanharProcessamento(consultar, eventos, { intervaloInicialMs: 1000, fator: 1, limiteMs: 3000 })

    await vi.advanceTimersByTimeAsync(3000)
    expect(eventos.aoEsgotar).toHaveBeenCalledOnce()

    await vi.advanceTimersByTimeAsync(60_000)
    expect(consultar).toHaveBeenCalledTimes(3)
  })

  it('falha pontual de rede não interrompe; erro definitivo interrompe', async () => {
    const definitivo = new Error('sessão expirada')
    const consultar = vi
      .fn()
      .mockRejectedValueOnce(new Error('rede'))
      .mockRejectedValueOnce(definitivo)
    acompanharProcessamento(consultar, eventos, {
      intervaloInicialMs: 1000,
      fator: 1,
      ehDefinitivo: (erro) => erro === definitivo,
    })

    await vi.advanceTimersByTimeAsync(2000)
    await vi.advanceTimersByTimeAsync(10_000)

    expect(consultar).toHaveBeenCalledTimes(2)
    expect(eventos.aoFalhar).toHaveBeenCalledWith(definitivo)
  })

  it('cancelar para as consultas, inclusive a que já estava em andamento', async () => {
    let responder: (valor: string) => void = () => {}
    const consultar = vi.fn(() => new Promise<string | null>((resolve) => (responder = resolve)))
    const cancelar = acompanharProcessamento(consultar, eventos, { intervaloInicialMs: 1000 })

    await vi.advanceTimersByTimeAsync(1000)
    cancelar()
    responder('CONCLUIDA')
    await vi.advanceTimersByTimeAsync(60_000)

    expect(consultar).toHaveBeenCalledTimes(1)
    expect(eventos.aoTerminar).not.toHaveBeenCalled()
  })
})
