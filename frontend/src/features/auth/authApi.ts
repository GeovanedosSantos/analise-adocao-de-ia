import { guardarToken, requisicao } from "@/api/cliente"

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
