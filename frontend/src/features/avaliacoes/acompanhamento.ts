type Eventos<T> = {
  aoTerminar: (resultado: T) => void
  /** O limite de tempo acabou e o processamento continua: a tela oferece verificar de novo. */
  aoEsgotar: () => void
  /** Erro em que não adianta tentar de novo (ex.: sessão expirada). */
  aoFalhar: (erro: unknown) => void
}

type Opcoes = {
  intervaloInicialMs?: number
  intervaloMaximoMs?: number
  fator?: number
  limiteMs?: number
  ehDefinitivo?: (erro: unknown) => boolean
}

/**
 * Consulta um processamento em segundo plano até ele terminar (RNF06). `consultar` devolve
 * `null` enquanto o processamento continua. As consultas se espaçam com o tempo e param
 * no limite, para a tela não ficar consultando para sempre se o worker estiver fora do ar.
 * Retorna a função que cancela o acompanhamento.
 */
export function acompanharProcessamento<T>(
  consultar: () => Promise<T | null>,
  { aoTerminar, aoEsgotar, aoFalhar }: Eventos<T>,
  {
    intervaloInicialMs = 3000,
    intervaloMaximoMs = 30_000,
    fator = 1.5,
    limiteMs = 5 * 60_000,
    ehDefinitivo = () => false,
  }: Opcoes = {},
) {
  let ativo = true
  let intervalo = intervaloInicialMs
  let decorrido = 0
  let timer: ReturnType<typeof setTimeout> | undefined

  function agendar() {
    if (decorrido >= limiteMs) {
      ativo = false
      aoEsgotar()
      return
    }
    const espera = Math.min(intervalo, limiteMs - decorrido)
    decorrido += espera
    intervalo = Math.min(intervalo * fator, intervaloMaximoMs)
    timer = setTimeout(() => void verificar(), espera)
  }

  // Uma consulta só começa depois que a anterior termina, mesmo com a rede lenta
  async function verificar() {
    try {
      const resultado = await consultar()
      if (!ativo) return
      if (resultado !== null) {
        ativo = false
        aoTerminar(resultado)
        return
      }
    } catch (erro) {
      if (!ativo) return
      if (ehDefinitivo(erro)) {
        ativo = false
        aoFalhar(erro)
        return
      }
      // Falha pontual de rede: tenta no próximo ciclo
    }
    agendar()
  }

  agendar()
  return () => {
    ativo = false
    clearTimeout(timer)
  }
}
