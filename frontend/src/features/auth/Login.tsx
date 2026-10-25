import { useState, type SubmitEvent } from 'react'
import { entrar } from './authApi'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao } from '@/components/Botao'

export function Login({ aoEntrar }: { aoEntrar: () => void }) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: SubmitEvent) {
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
    <div className="flex w-full max-w-sm flex-col gap-8">
      <h1 className="m-0 text-center text-3xl text-balance sm:text-4xl">Análise de adoção de IA</h1>
      <form onSubmit={enviar} className="flex flex-col gap-4 rounded-xl border border-borda bg-superficie p-6">
        <h2>Entrar</h2>
        <label className="flex flex-col gap-1 text-sm">
          Usuário
          <input
            className="rounded border border-borda bg-superficie px-3 py-2 text-titulo"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Senha
          <input
            className="rounded border border-borda bg-superficie px-3 py-2 text-titulo"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {erro && <Alerta tipo="erro">{erro}</Alerta>}
        <Botao type="submit" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </Botao>
      </form>
    </div>
  )
}
