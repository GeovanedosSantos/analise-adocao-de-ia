import { useRef, useState, type SubmitEvent } from 'react'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { Campo } from '@/components/Campo'
import { cadastrar } from './authApi'
import { BotaoGoogle, DivisorOu } from './BotaoGoogle'
import { MolduraAuth } from './MolduraAuth'
import { CampoSetor } from './CampoSetor'
import { errosDoServidor, validarCadastro, type ErrosCampos } from './validacao'

const VAZIO = { nome: '', email: '', empresa_nome: '', empresa_setor: '', senha: '', confirmacao: '' }

/** Cadastro de uma empresa e do primeiro usuário dela. Ao terminar, a sessão já começa. */
export function Cadastro({ aoEntrar }: { aoEntrar: () => void }) {
  const [dados, setDados] = useState(VAZIO)
  const [erros, setErros] = useState<ErrosCampos>({})
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  // Depois da primeira tentativa, os erros somem conforme a pessoa corrige
  const [tentou, setTentou] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const formulario = useRef<HTMLFormElement>(null)

  function alterar(campo: keyof typeof VAZIO) {
    return (valor: string) => {
      const novos = { ...dados, [campo]: valor }
      setDados(novos)
      if (tentou) setErros(validarCadastro(novos))
    }
  }

  function focarPrimeiroErro() {
    requestAnimationFrame(() => formulario.current?.querySelector<HTMLInputElement>('[aria-invalid="true"]')?.focus())
  }

  async function enviar(evento: SubmitEvent) {
    evento.preventDefault()
    if (enviando) return
    setTentou(true)
    setErroGeral(null)
    const encontrados = validarCadastro(dados)
    setErros(encontrados)
    if (Object.keys(encontrados).length > 0) return focarPrimeiroErro()

    setEnviando(true)
    try {
      await cadastrar({
        nome: dados.nome.trim(),
        email: dados.email.trim(),
        empresa_nome: dados.empresa_nome.trim(),
        empresa_setor: dados.empresa_setor.trim(),
        senha: dados.senha,
      })
      aoEntrar()
    } catch (e) {
      if (e instanceof ErroApi && e.status === 400) {
        const { campos, geral } = errosDoServidor(e.detalhes)
        setErros(campos)
        setErroGeral(geral ?? null)
        focarPrimeiroErro()
      } else if (e instanceof ErroApi && e.status === 429) {
        setErroGeral('Muitas tentativas em pouco tempo. Aguarde um minuto e tente de novo.')
      } else {
        setErroGeral('Não foi possível criar a conta agora. Verifique a conexão e tente de novo.')
      }
      setEnviando(false)
    }
  }

  const contaComErro = Object.keys(erros).length

  return (
    <MolduraAuth
      titulo="Criar conta"
      descricao="Cadastre sua empresa para responder ao questionário e acompanhar a prontidão para IA."
      largura="media"
      acoesCabecalho={
        <BotaoLink to="/login" variante="secundario" className="h-9 px-3">
          Entrar
        </BotaoLink>
      }
      rodape={
        <>
          Já tem uma conta?{' '}
          <Link to="/login" className="font-medium text-destaque underline-offset-4 hover:underline">
            Entrar
          </Link>
        </>
      }
    >
      <BotaoGoogle />
      <DivisorOu />

      <form ref={formulario} onSubmit={enviar} noValidate className="flex flex-col gap-5" aria-busy={enviando}>
        <fieldset className="flex flex-col gap-4">
          <legend className="mb-3 text-xs font-medium tracking-wide uppercase">Seus dados</legend>
          <Campo
            rotulo="Nome"
            value={dados.nome}
            onChange={(e) => alterar('nome')(e.target.value)}
            erro={erros.nome}
            autoComplete="name"
            maxLength={150}
            required
          />
          <Campo
            rotulo="E-mail"
            type="email"
            value={dados.email}
            onChange={(e) => alterar('email')(e.target.value)}
            erro={erros.email}
            dica="Você vai usar este e-mail para entrar."
            autoComplete="email"
            autoCapitalize="none"
            inputMode="email"
            maxLength={254}
            required
          />
        </fieldset>

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-3 text-xs font-medium tracking-wide uppercase">Empresa</legend>
          <Campo
            rotulo="Nome da empresa"
            value={dados.empresa_nome}
            onChange={(e) => alterar('empresa_nome')(e.target.value)}
            erro={erros.empresa_nome}
            autoComplete="organization"
            maxLength={255}
            required
          />
          <CampoSetor valor={dados.empresa_setor} aoAlterar={alterar('empresa_setor')} erro={erros.empresa_setor} />
        </fieldset>

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-3 text-xs font-medium tracking-wide uppercase">Senha</legend>
          <Campo
            rotulo="Senha"
            type="password"
            value={dados.senha}
            onChange={(e) => alterar('senha')(e.target.value)}
            erro={erros.senha}
            dica="Pelo menos 8 caracteres. Evite senhas óbvias ou parecidas com seu nome."
            autoComplete="new-password"
            required
          />
          <Campo
            rotulo="Repita a senha"
            type="password"
            value={dados.confirmacao}
            onChange={(e) => alterar('confirmacao')(e.target.value)}
            erro={erros.confirmacao}
            autoComplete="new-password"
            required
          />
        </fieldset>

        {erroGeral ? (
          <Alerta tipo="erro">{erroGeral}</Alerta>
        ) : (
          tentou &&
          contaComErro > 0 && (
            <Alerta tipo="erro">
              {contaComErro === 1 ? 'Corrija o campo destacado.' : `Corrija os ${contaComErro} campos destacados.`}
            </Alerta>
          )
        )}

        <Botao type="submit" disabled={enviando} className="group h-11 w-full">
          {enviando ? 'Criando conta…' : 'Criar conta'}
          {!enviando && (
            <ArrowRight size={16} aria-hidden className="transition-transform duration-150 ease-saida group-hover:translate-x-0.5" />
          )}
        </Botao>
      </form>
    </MolduraAuth>
  )
}
