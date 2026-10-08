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