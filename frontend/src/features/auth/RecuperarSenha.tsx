import { useState, type ReactNode, type SubmitEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { CLASSE_CAMPO as CAMPO } from '@/components/Campo'
import { pedirRedefinicao, redefinirSenha } from './authApi'
import { MolduraAuth } from './MolduraAuth'

/** "Esqueci a minha senha" (UC01 FA01): pede o e-mail e envia o link de redefinição. */
export function PaginaEsqueciSenha() {
  const [email, setEmail] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function enviar(evento: SubmitEvent) {
    evento.preventDefault()
    setEnviando(true)
    setErro(null)
    try {
      await pedirRedefinicao(email)
      setEnviado(true)
    } catch (e) {
      setErro(e instanceof ErroApi && e.status === 429 ? 'Muitas tentativas. Aguarde um minuto.' : 'Não foi possível enviar agora.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Moldura titulo="Recuperar senha">
      {enviado ? (
        <Alerta tipo="sucesso" titulo="Verifique seu e-mail">
          Se o e-mail estiver cadastrado, você vai receber um link para criar uma nova senha.
        </Alerta>
      ) : (
        <form onSubmit={enviar} className="flex flex-col gap-4">
          <p className="text-sm">Informe o e-mail cadastrado e enviaremos um link para criar uma nova senha.</p>
          <label className="flex flex-col gap-1.5 text-sm font-medium text-titulo">
            E-mail
            <input
              className={CAMPO}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>
          {erro && <Alerta tipo="erro">{erro}</Alerta>}
          <Botao type="submit" disabled={enviando} className="h-11 w-full">
            {enviando ? 'Enviando…' : 'Enviar link'}
          </Botao>
        </form>
      )}
    </Moldura>
  )
}

/** Abre pelo link do e-mail (?uid=…&token=…) e grava a nova senha. */
export function PaginaRedefinirSenha() {
  const [parametros] = useSearchParams()
  const uid = parametros.get('uid') ?? ''
  const token = parametros.get('token') ?? ''
  const [senha, setSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [pronto, setPronto] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function enviar(evento: SubmitEvent) {
    evento.preventDefault()
    if (senha !== confirmacao) return setErro('As senhas não conferem.')
    setEnviando(true)
    setErro(null)
    try {
      await redefinirSenha(uid, token, senha)
      setPronto(true)
    } catch (e) {
      const detalhes = e instanceof ErroApi ? (e.detalhes as { detail?: string; nova_senha?: string[] } | null) : null
      setErro(detalhes?.nova_senha?.join(' ') ?? detalhes?.detail ?? 'Não foi possível redefinir a senha.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Moldura titulo="Nova senha">
      {pronto ? (
        <div className="flex flex-col gap-4">
          <Alerta tipo="sucesso" titulo="Senha alterada">
            Agora é só entrar com a nova senha.
          </Alerta>
          <BotaoLink to="/login" className="h-11 w-full">
            Ir para o login
          </BotaoLink>
        </div>
      ) : !uid || !token ? (
        <Alerta tipo="erro">O link está incompleto. Peça um novo em “Esqueci a minha senha”.</Alerta>
      ) : (
        <form onSubmit={enviar} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5 text-sm font-medium text-titulo">
            Nova senha
            <input className={CAMPO} type="password" value={senha} onChange={(e) => setSenha(e.target.value)} autoComplete="new-password" required />
          </label>
          <label className="flex flex-col gap-1.5 text-sm font-medium text-titulo">
            Repita a nova senha
            <input
              className={CAMPO}
              type="password"
              value={confirmacao}
              onChange={(e) => setConfirmacao(e.target.value)}
              autoComplete="new-password"
              required
            />
          </label>
          {erro && <Alerta tipo="erro">{erro}</Alerta>}
          <Botao type="submit" disabled={enviando} className="h-11 w-full">
            {enviando ? 'Salvando…' : 'Salvar nova senha'}
          </Botao>
        </form>
      )}
    </Moldura>
  )
}

function Moldura({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <MolduraAuth
      titulo={titulo}
      rodape={
        <Link to="/login" className="text-destaque underline-offset-4 hover:underline">
          Voltar para o login
        </Link>
      }
    >
      {children}
    </MolduraAuth>
  )
}
