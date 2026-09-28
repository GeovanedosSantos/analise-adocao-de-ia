const CHAVE_TOKEN = 'token_acesso'

export class ErroApi extends Error {
  status: number
  detalhes: unknown

  constructor(status: number, detalhes: unknown) {
    super(`Erro ${status} na API`)
    this.status = status
    this.detalhes = detalhes
  }
}

export function lerToken(): string | null {
  try {
    return sessionStorage.getItem(CHAVE_TOKEN)
  } catch {
    return null
  }
}

export function guardarToken(token: string | null) {
  try {
    if (token) sessionStorage.setItem(CHAVE_TOKEN, token)
    else sessionStorage.removeItem(CHAVE_TOKEN)
  } catch {
    // Sem storage (modo privado): o login dura só até recarregar a página
  }
}

type Opcoes = { metodo?: 'GET' | 'POST' | 'PATCH'; corpo?: unknown }

export type RespostaApi<T> = { status: number; dados: T }

/** Chama a API v1. O Vite encaminha /api para o Django em desenvolvimento. */
export async function requisicao<T>(caminho: string, { metodo = 'GET', corpo }: Opcoes = {}): Promise<RespostaApi<T>> {
  const token = lerToken()
  const resposta = await fetch(`/api/v1${caminho}`, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  })
  const dados = resposta.status === 204 ? null : await resposta.json().catch(() => null)
  if (!resposta.ok) throw new ErroApi(resposta.status, dados)
  return { status: resposta.status, dados: dados as T }
}
