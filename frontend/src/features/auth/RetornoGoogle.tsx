import { useEffect, useRef, useState, type SubmitEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { Campo } from '@/components/Campo'
import { concluirCadastroGoogle, descartarPendenciaGoogle, entrarComGoogle, lerPendenciaGoogle } from './authApi'
import { BotaoGoogle } from './BotaoGoogle'
import { CampoSetor } from './CampoSetor'
import { MolduraAuth } from './MolduraAuth'
import { errosDoServidor, validarEmpresa, type ErrosCampos } from './validacao'

type Estado =
  | { tipo: 'conferindo' }
  | { tipo: 'cadastro'; token: string; email: string; nome: string }
  | { tipo: 'conflito'; mensagem: string }
  | { tipo: 'erro'; titulo: string; mensagem: string }

const LINKS_VOLTA = (
  <div className="flex flex-wrap gap-2">
    <BotaoLink to="/login" variante="secundario">
      Voltar para o login
    </BotaoLink>
    <BotaoLink to="/cadastro" variante="secundario">
      Criar conta com e-mail
    </BotaoLink>
  </div>
)

function detalhe(e: unknown) {
  const detalhes = e instanceof ErroApi ? (e.detalhes as { detail?: string } | null) : null
  return detalhes?.detail
}

type Inicio = { tipo: 'trocar'; code: string; verifier: string } | Extract<Estado, { tipo: 'erro' }>

/** Decide, só com a URL e o que foi guardado na aba, se dá para trocar o código ou se já é um erro. */
function analisarRetorno(parametros: URLSearchParams): Inicio {
  const code = parametros.get('code')
  const erroGoogle = parametros.get('error')
  if (erroGoogle === 'access_denied') {
    return { tipo: 'erro', titulo: 'Entrada cancelada', mensagem: 'Você cancelou a entrada com o Google. Nada foi alterado.' }
  }
  if (erroGoogle || !code) {
    return { tipo: 'erro', titulo: 'O Google não concluiu a entrada', mensagem: 'Tente de novo ou use seu e-mail e senha.' }
  }
  const verifier = lerPendenciaGoogle(parametros.get('state'))
  if (!verifier) {
    return {
      tipo: 'erro',
      titulo: 'Não foi possível confirmar o retorno',
      mensagem: 'A volta do Google não corresponde a uma entrada iniciada nesta aba. Tente de novo pelo botão abaixo.',
    }
  }
  return { tipo: 'trocar', code, verifier }
}

/**
 * Volta do Google (/entrar/google/retorno?code=…&state=…). Confere o state guardado antes de sair,
 * troca o código no servidor e, se a conta for nova, pede os dados da empresa.
 */
export function RetornoGoogle({ aoEntrar, destino }: { aoEntrar: () => void; destino: string }) {
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const [inicio] = useState(() => analisarRetorno(parametros))
  const [estado, setEstado] = useState<Estado>(inicio.tipo === 'trocar' ? { tipo: 'conferindo' } : inicio)
  // O código do Google só vale uma vez: a troca não pode rodar de novo (StrictMode roda efeitos duas vezes)
  const iniciou = useRef(false)

  useEffect(() => {
    if (iniciou.current) return
    iniciou.current = true
    descartarPendenciaGoogle()
    // Tira o código da barra de endereço e do histórico
    window.history.replaceState(null, '', window.location.pathname)
    if (inicio.tipo !== 'trocar') return

    entrarComGoogle(inicio.code, inicio.verifier)
      .then((resposta) => {
        if (resposta.tipo === 'sessao') {
          aoEntrar()
          navegar(destino, { replace: true })
        } else {
          setEstado({ tipo: 'cadastro', token: resposta.token_cadastro, email: resposta.email, nome: resposta.nome })
        }
      })
      .catch((e) => {
        if (e instanceof ErroApi && e.status === 409) {
          setEstado({ tipo: 'conflito', mensagem: detalhe(e) ?? 'Já existe uma conta com este e-mail.' })
        } else if (e instanceof ErroApi && e.status === 429) {
          setEstado({ tipo: 'erro', titulo: 'Muitas tentativas', mensagem: 'Aguarde um minuto e tente de novo.' })
        } else {
          setEstado({
            tipo: 'erro',
            titulo: 'Não foi possível entrar com o Google',
            mensagem: detalhe(e) ?? 'Verifique a conexão e tente de novo.',
          })
        }
      })
  }, [inicio, aoEntrar, navegar, destino])

  if (estado.tipo === 'cadastro') {
    return (
      <ConcluirCadastro
        {...estado}
        aoConcluir={() => {
          aoEntrar()
          navegar(destino, { replace: true })
        }}
        aoFalhar={(proximo) => setEstado(proximo)}
      />
    )
  }

  if (estado.tipo === 'conferindo') {
    return (
      <MolduraAuth titulo="Entrando com o Google">
        <p role="status" className="text-sm">
          Conferindo seu acesso…
        </p>
      </MolduraAuth>
    )
  }

  if (estado.tipo === 'conflito') {
    return (
      <MolduraAuth titulo="Este e-mail já tem conta">
        <Alerta tipo="aviso">{estado.mensagem}</Alerta>
        <div className="flex flex-wrap gap-2">
          <BotaoLink to="/login">Entrar com e-mail e senha</BotaoLink>
          <BotaoLink to="/recuperar-senha" variante="secundario">
            Esqueci a minha senha
          </BotaoLink>
        </div>
      </MolduraAuth>
    )
  }

  return (
    <MolduraAuth titulo={estado.titulo}>
      <Alerta tipo="erro">{estado.mensagem}</Alerta>
      <BotaoGoogle />
      {LINKS_VOLTA}
    </MolduraAuth>
  )
}

type PropsConcluir = {
  token: string
  email: string
  nome: string
  aoConcluir: () => void
  aoFalhar: (estado: Estado) => void
}

/** Segunda etapa da conta nova pelo Google: só falta a empresa. */
function ConcluirCadastro({ token, email, nome, aoConcluir, aoFalhar }: PropsConcluir) {
  const [empresa, setEmpresa] = useState({ empresa_nome: '', empresa_setor: '' })
  const [erros, setErros] = useState<ErrosCampos>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const formulario = useRef<HTMLFormElement>(null)

  async function enviar(evento: SubmitEvent) {
    evento.preventDefault()
    if (enviando) return
    setErroGeral(null)
    const encontrados = validarEmpresa(empresa)
    setErros(encontrados)
    if (Object.keys(encontrados).length > 0) {
      requestAnimationFrame(() => formulario.current?.querySelector<HTMLInputElement>('[aria-invalid="true"]')?.focus())
      return
    }
    setEnviando(true)
    try {
      await concluirCadastroGoogle(token, { empresa_nome: empresa.empresa_nome.trim(), empresa_setor: empresa.empresa_setor.trim() })
      aoConcluir()
    } catch (e) {
      setEnviando(false)
      if (e instanceof ErroApi && e.status === 409) {
        return aoFalhar({ tipo: 'conflito', mensagem: detalhe(e) ?? 'Já existe uma conta com este e-mail.' })
      }
      if (e instanceof ErroApi && e.status === 400) {
        const { campos, geral } = errosDoServidor(e.detalhes)
        if (Object.keys(campos).length === 0 && geral) {
          // Token de cadastro vencido: precisa voltar ao Google
          return aoFalhar({ tipo: 'erro', titulo: 'O tempo para concluir acabou', mensagem: geral })
        }
        setErros(campos)
        return
      }
      setErroGeral('Não foi possível concluir agora. Verifique a conexão e tente de novo.')
    }
  }

  return (
    <MolduraAuth
      titulo="Falta pouco"
      descricao={
        <>
          Você entrou como <strong className="font-medium break-all text-titulo">{email}</strong>
          {nome ? ` (${nome})` : ''}. Informe a empresa para criar a conta.
        </>
      }
      rodape={
        <Link to="/login" className="text-destaque underline-offset-4 hover:underline">
          Cancelar e voltar para o login
        </Link>
      }
    >
      <form ref={formulario} onSubmit={enviar} noValidate className="flex flex-col gap-4" aria-busy={enviando}>
        <Campo
          rotulo="Nome da empresa"
          value={empresa.empresa_nome}
          onChange={(e) => setEmpresa({ ...empresa, empresa_nome: e.target.value })}
          erro={erros.empresa_nome}
          autoComplete="organization"
          maxLength={255}
          required
        />
        <CampoSetor
          valor={empresa.empresa_setor}
          aoAlterar={(valor) => setEmpresa({ ...empresa, empresa_setor: valor })}
          erro={erros.empresa_setor}
        />
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}
        <Botao type="submit" disabled={enviando} className="h-11 w-full">
          {enviando ? 'Criando conta…' : 'Criar conta'}
        </Botao>
      </form>
    </MolduraAuth>
  )
}
