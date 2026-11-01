import { useRef, useState, type PointerEvent, type SubmitEvent } from 'react'
import { ArrowRight, Eye, EyeOff } from 'lucide-react'
import { Link } from 'react-router'
import { entrar } from './authApi'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { CabecalhoPublico } from '@/components/CabecalhoPublico'
import { CLASSE_CAMPO as CAMPO } from '@/components/Campo'
import { BotaoGoogle, DivisorOu } from './BotaoGoogle'
import { Mascote, type EstadoMascote } from './Mascote'
import { CLASSE_CARTAO_AUTH } from './MolduraAuth'

const RAIO_BRILHO = 320

type Foco = 'usuario' | 'senha' | null

/**
 * Tela de entrada (UC01): logo, tema e "Criar conta" no topo; a mascote Ada e o formulário no centro.
 * Aceita usuário ou e-mail, e a entrada com Google. Segue o tema escolhido.
 */
export function Login({ aoEntrar }: { aoEntrar: () => void }) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [senhaVisivel, setSenhaVisivel] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [foco, setFoco] = useState<Foco>(null)
  // Conta as falhas: a mascote fica triste até a pessoa voltar a digitar, e treme de novo a cada falha
  const [falhas, setFalhas] = useState(0)
  const [triste, setTriste] = useState(false)

  const brilho = useRef<HTMLDivElement>(null)
  const quadro = useRef(0)

  // Escreve direto no style (sem setState): o React não re-renderiza a cada movimento do mouse
  function moverLuz(evento: PointerEvent<HTMLElement>) {
    const caixa = evento.currentTarget.getBoundingClientRect()
    const x = evento.clientX - caixa.left
    const y = evento.clientY - caixa.top
    cancelAnimationFrame(quadro.current)
    quadro.current = requestAnimationFrame(() => {
      // Só transform: composição na GPU, sem repintar
      if (brilho.current) brilho.current.style.transform = `translate(${x - RAIO_BRILHO}px, ${y - RAIO_BRILHO}px)`
    })
  }

  function digitar(alterar: (valor: string) => void) {
    return (valor: string) => {
      alterar(valor)
      setTriste(false)
    }
  }

  async function enviar(evento: SubmitEvent) {
    evento.preventDefault()
    setEnviando(true)
    setErro(null)
    try {
      await entrar(usuario, senha)
      aoEntrar()
    } catch (e) {
      setErro(e instanceof ErroApi && e.status === 401 ? 'Usuário, e-mail ou senha incorretos.' : 'Não foi possível entrar.')
      setTriste(true)
      setFalhas((n) => n + 1)
    } finally {
      setEnviando(false)
    }
  }

  const estado: EstadoMascote = enviando
    ? 'pensando'
    : triste
      ? 'triste'
      : foco === 'senha'
        ? senhaVisivel
          ? 'espiando'
          : 'senha'
        : foco === 'usuario'
          ? 'usuario'
          : 'ocioso'

  return (
    <main onPointerMove={moverLuz} className="relative isolate flex flex-1 flex-col overflow-hidden bg-fundo">
      {/* Fundo: duas manchas de luz fixas (gradientes, sem imagem) e um brilho que segue o cursor */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-1/3 -left-1/4 size-[60rem] rounded-full bg-[radial-gradient(circle,rgba(65,105,225,0.14),transparent_60%)] dark:bg-[radial-gradient(circle,rgba(65,105,225,0.22),transparent_60%)]" />
        <div className="absolute -right-1/4 -bottom-1/3 size-[56rem] rounded-full bg-[radial-gradient(circle,rgba(124,92,230,0.10),transparent_60%)] dark:bg-[radial-gradient(circle,rgba(124,92,230,0.16),transparent_60%)]" />
        <div
          ref={brilho}
          style={{
            width: RAIO_BRILHO * 2,
            height: RAIO_BRILHO * 2,
            transform: `translate(calc(50vw - ${RAIO_BRILHO}px), calc(45vh - ${RAIO_BRILHO}px))`,
          }}
          className="absolute top-0 left-0 rounded-full bg-[radial-gradient(circle,rgba(65,105,225,0.12),transparent_65%)] will-change-transform dark:bg-[radial-gradient(circle,rgba(65,105,225,0.2),transparent_65%)]"
        />
      </div>

      <CabecalhoPublico
        acoes={
          <BotaoLink to="/cadastro" variante="secundario" className="h-9 px-3">
            Criar conta
          </BotaoLink>
        }
      />

      <div className="flex flex-1 items-center justify-center px-4 pb-16 sm:px-6">
        {/* Entra uma vez, ao abrir a página: fade e 8px de subida, 300 ms ease-out (só opacidade se o sistema pedir menos movimento) */}
        <div className="flex w-full max-w-sm flex-col transition-[opacity,translate] duration-300 ease-saida starting:opacity-0 motion-safe:starting:translate-y-2">
          {/* A mascote "senta" na borda do cartão; a key faz ela tremer de novo a cada falha */}
          <div
            key={falhas}
            className={`relative z-10 -mb-3 pl-2 ${falhas > 0 ? 'motion-safe:animate-[tremer_400ms_ease-out]' : ''}`}
          >
            <Mascote estado={estado} />
          </div>

          <div className={CLASSE_CARTAO_AUTH}>
            <form onSubmit={enviar} className="flex flex-col gap-4" aria-busy={enviando}>
              <h1 className="sr-only">Entrar</h1>
              <label className="flex flex-col gap-1.5 text-sm font-medium text-titulo">
                Usuário ou e-mail
                <input
                  className={CAMPO}
                  value={usuario}
                  onChange={(e) => digitar(setUsuario)(e.target.value)}
                  onFocus={() => setFoco('usuario')}
                  onBlur={() => setFoco(null)}
                  autoComplete="username"
                  autoCapitalize="none"
                  placeholder="seu.usuario ou voce@empresa.com"
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm font-medium text-titulo">
                Senha
                <span className="relative">
                  <input
                    className={`${CAMPO} pr-11`}
                    type={senhaVisivel ? 'text' : 'password'}
                    value={senha}
                    onChange={(e) => digitar(setSenha)(e.target.value)}
                    onFocus={() => setFoco('senha')}
                    onBlur={() => setFoco(null)}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setSenhaVisivel((v) => !v)}
                    // Mantém o foco na senha: a mascote não "perde" o estado ao clicar no olho
                    onPointerDown={(e) => e.preventDefault()}
                    aria-label={senhaVisivel ? 'Ocultar senha' : 'Mostrar senha'}
                    aria-pressed={senhaVisivel}
                    className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-lg text-texto hover:text-titulo focus-visible:outline-2 focus-visible:outline-destaque"
                  >
                    {senhaVisivel ? <EyeOff size={18} aria-hidden /> : <Eye size={18} aria-hidden />}
                  </button>
                </span>
              </label>

              <Link to="/recuperar-senha" className="-mt-2 self-end text-sm text-destaque underline-offset-4 hover:underline">
                Esqueci a minha senha
              </Link>

              {erro && <Alerta tipo="erro">{erro}</Alerta>}

              <Botao type="submit" disabled={enviando} className="group mt-2 h-11 w-full">
                {enviando ? 'Entrando…' : 'Entrar'}
                {!enviando && (
                  <ArrowRight size={16} aria-hidden className="transition-transform duration-150 ease-saida group-hover:translate-x-0.5" />
                )}
              </Botao>
            </form>
            <DivisorOu />
            <BotaoGoogle />
          </div>
          <p className="mt-4 text-center text-sm">
            Ainda não tem conta?{' '}
            <Link to="/cadastro" className="font-medium text-destaque underline-offset-4 hover:underline">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
