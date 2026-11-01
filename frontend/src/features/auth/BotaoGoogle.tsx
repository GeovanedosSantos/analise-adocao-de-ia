import { useEffect, useState } from 'react'
import { Botao } from '@/components/Botao'
import { iniciarGoogle, lerConfigGoogle, type ConfigGoogle } from './authApi'

// Uma busca por carregamento da página: login e cadastro compartilham a resposta
let configPromessa: Promise<ConfigGoogle> | null = null
function configGoogle() {
  configPromessa ??= lerConfigGoogle().catch((erro) => {
    configPromessa = null
    throw erro
  })
  return configPromessa
}

type Estado = { tipo: 'carregando' } | { tipo: 'pronto'; config: ConfigGoogle } | { tipo: 'falhou' }

/**
 * "Continuar com o Google" (login e cadastro). Leva ao Google com PKCE; a volta é tratada em RetornoGoogle.
 * Sem credenciais no servidor, o botão aparece desabilitado com o motivo, em vez de sumir.
 */
export function BotaoGoogle() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })
  const [saindo, setSaindo] = useState(false)

  useEffect(() => {
    let ativo = true
    configGoogle()
      .then((config) => ativo && setEstado({ tipo: 'pronto', config }))
      .catch(() => ativo && setEstado({ tipo: 'falhou' }))
    return () => {
      ativo = false
    }
  }, [])

  const config = estado.tipo === 'pronto' && estado.config.habilitado ? estado.config : null
  const aviso =
    estado.tipo === 'falhou'
      ? 'Não foi possível verificar a entrada com Google. Recarregue a página para tentar de novo.'
      : estado.tipo === 'pronto' && !estado.config.habilitado
        ? 'A entrada com Google ainda não foi configurada neste ambiente.'
        : null

  async function continuar() {
    if (!config) return
    setSaindo(true)
    try {
      await iniciarGoogle(config)
    } catch {
      // Sem crypto.subtle (página fora de HTTPS) ou sem sessionStorage
      setSaindo(false)
      setEstado({ tipo: 'falhou' })
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Botao
        variante="secundario"
        onClick={continuar}
        disabled={!config || saindo}
        aria-describedby={aviso ? 'aviso-google' : undefined}
        className="h-11 w-full"
      >
        <IconeGoogle />
        {saindo ? 'Abrindo o Google…' : 'Continuar com o Google'}
      </Botao>
      {aviso && (
        <p id="aviso-google" className="text-center text-xs">
          {aviso}
        </p>
      )}
    </div>
  )
}

/** Marca "G" do Google, nas cores oficiais, como pedem as diretrizes de botões de login do Google. */
function IconeGoogle() {
  return (
    <svg viewBox="0 0 48 48" className="size-[18px] shrink-0" aria-hidden>
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
  )
}

/** Separador "ou" entre o formulário e o botão do Google. */
export function DivisorOu() {
  return (
    <div className="flex items-center gap-3 text-xs tracking-wide uppercase" role="presentation">
      <span className="h-px flex-1 bg-borda" />
      ou
      <span className="h-px flex-1 bg-borda" />
    </div>
  )
}
