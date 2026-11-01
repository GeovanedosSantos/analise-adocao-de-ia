import { guardarToken, requisicao } from '@/api/cliente'

type Tokens = { access: string; refresh: string }

export async function entrar(username: string, password: string) {
  const { dados } = await requisicao<{ access: string }>('/auth/token/', {
    metodo: 'POST',
    corpo: { username, password },
  })
  guardarToken(dados.access)
}

export function sair() {
  guardarToken(null)
}

/** Envia o link de redefinição; responde igual mesmo se o e-mail não existir. */
export async function pedirRedefinicao(email: string) {
  await requisicao('/auth/senha/esqueci/', { metodo: 'POST', corpo: { email } })
}

export async function redefinirSenha(uid: string, token: string, novaSenha: string) {
  await requisicao('/auth/senha/redefinir/', { metodo: 'POST', corpo: { uid, token, nova_senha: novaSenha } })
}

export type DadosEmpresa = { empresa_nome: string; empresa_setor: string }
export type DadosCadastro = DadosEmpresa & { nome: string; email: string; senha: string }

/** Cria a empresa e a conta. A sessão já começa: a senha só passa por esta requisição, nada fica guardado. */
export async function cadastrar(dados: DadosCadastro) {
  const resposta = await requisicao<Tokens>('/auth/cadastro/', { metodo: 'POST', corpo: dados })
  guardarToken(resposta.dados.access)
}

// Google (OpenID Connect, fluxo de autorização com PKCE) ---------------------------------------

export type ConfigGoogle = { habilitado: false } | { habilitado: true; client_id: string; redirect_uri: string }

export async function lerConfigGoogle() {
  return (await requisicao<ConfigGoogle>('/auth/google/config/')).dados
}

const CHAVE_GOOGLE = 'google_pkce'
type PendenciaGoogle = { state: string; verifier: string }

function aleatorio(bytes: number) {
  return base64Url(crypto.getRandomValues(new Uint8Array(bytes)))
}

function base64Url(bytes: Uint8Array) {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

/** Leva a pessoa para a tela de escolha de conta do Google. O retorno cai em /entrar/google/retorno. */
export async function iniciarGoogle(config: Extract<ConfigGoogle, { habilitado: true }>) {
  const state = aleatorio(24)
  const verifier = aleatorio(48)
  const desafio = base64Url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))))
  // sessionStorage: o verificador vale só para esta aba e some ao fechá-la
  sessionStorage.setItem(CHAVE_GOOGLE, JSON.stringify({ state, verifier } satisfies PendenciaGoogle))

  const url = new URL('https://accounts.google.com/o/oauth2/v2/auth')
  url.search = new URLSearchParams({
    client_id: config.client_id,
    redirect_uri: config.redirect_uri,
    response_type: 'code',
    scope: 'openid email profile',
    state,
    code_challenge: desafio,
    code_challenge_method: 'S256',
    prompt: 'select_account',
  }).toString()
  window.location.assign(url)
}

/** Devolve o verificador guardado antes de ir ao Google, só se o state de volta for o mesmo. */
export function lerPendenciaGoogle(stateRecebido: string | null): string | null {
  try {
    const pendencia = JSON.parse(sessionStorage.getItem(CHAVE_GOOGLE) ?? 'null') as PendenciaGoogle | null
    if (!pendencia || !stateRecebido || pendencia.state !== stateRecebido) return null
    return pendencia.verifier
  } catch {
    return null
  }
}

/** O código do Google só vale uma vez: depois de usar (ou recusar) o retorno, a pendência é apagada. */
export function descartarPendenciaGoogle() {
  try {
    sessionStorage.removeItem(CHAVE_GOOGLE)
  } catch {
    // Sem storage: não há o que apagar
  }
}

export type RespostaGoogle =
  | { tipo: 'sessao' }
  | { tipo: 'cadastro'; token_cadastro: string; email: string; nome: string }

export async function entrarComGoogle(code: string, codeVerifier: string): Promise<RespostaGoogle> {
  const { dados } = await requisicao<Tokens | { cadastro_pendente: true; token_cadastro: string; email: string; nome: string }>(
    '/auth/google/',
    { metodo: 'POST', corpo: { code, code_verifier: codeVerifier } },
  )
  if ('access' in dados) {
    guardarToken(dados.access)
    return { tipo: 'sessao' }
  }
  return { tipo: 'cadastro', token_cadastro: dados.token_cadastro, email: dados.email, nome: dados.nome }
}

export async function concluirCadastroGoogle(tokenCadastro: string, empresa: DadosEmpresa) {
  const { dados } = await requisicao<Tokens>('/auth/google/concluir/', {
    metodo: 'POST',
    corpo: { token_cadastro: tokenCadastro, ...empresa },
  })
  guardarToken(dados.access)
}
