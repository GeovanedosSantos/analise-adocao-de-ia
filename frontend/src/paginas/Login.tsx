import { useState, type FormEvent } from 'react'
import { entrar } from '../api/avaliacoes'
import { ErroApi } from '../api/cliente'

export function Login({ aoEntrar }: { aoEntrar: () => void }) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    setErro(null)
    try {
      await entrar(usuario, senha)
      aoEntrar()
    } catch (e) {
      setErro(e instanceof ErroApi && e.status === 401 ? 'Usuário ou senha incorretos.' : 'Não foi possível entrar.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto flex w-full max-w-sm flex-col gap-4 p-6">
      <h2>Entrar</h2>
      <label className="flex flex-col gap-1 text-sm">
        Usuário
        <input
          className="rounded border border-borda bg-fundo px-3 py-2 text-titulo"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="username"
          required
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Senha
        <input
          className="rounded border border-borda bg-fundo px-3 py-2 text-titulo"
          type="password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>
      {erro && <p role="alert" className="text-sm text-red-600">{erro}</p>}
      <button
        type="submit"
        disabled={enviando}
        className="rounded bg-destaque px-4 py-2 font-medium text-white disabled:opacity-60"
      >
        {enviando ? 'Entrando…' : 'Entrar'}
      </button>
    </form>
  )
}
