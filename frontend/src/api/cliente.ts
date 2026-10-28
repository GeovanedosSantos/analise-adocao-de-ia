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

function cabecalhoAutorizacao(): Record<string, string> {
  const token = lerToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** Chama a API v1. O Vite encaminha /api para o Django em desenvolvimento. */
export async function requisicao<T>(caminho: string, { metodo = 'GET', corpo }: Opcoes = {}): Promise<RespostaApi<T>> {
  const resposta = await fetch(`/api/v1${caminho}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', ...cabecalhoAutorizacao() },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  })
  const dados = resposta.status === 204 ? null : await resposta.json().catch(() => null)
  if (!resposta.ok) throw new ErroApi(resposta.status, dados)
  return { status: resposta.status, dados: dados as T }
}

/** Baixa um arquivo da API v1 (ex.: o PDF) e oferece para salvar. Erros vêm como ErroApi com o JSON de detalhe. */
export async function baixarArquivo(caminho: string, nomePadrao: string) {
  const resposta = await fetch(`/api/v1${caminho}`, { headers: cabecalhoAutorizacao() })
  if (!resposta.ok) throw new ErroApi(resposta.status, await resposta.json().catch(() => null))
  // O nome vem do Content-Disposition: attachment; filename="..."
  const nome = resposta.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] ?? nomePadrao
  const url = URL.createObjectURL(await resposta.blob())
  const link = Object.assign(document.createElement('a'), { href: url, download: nome })
  document.body.append(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
