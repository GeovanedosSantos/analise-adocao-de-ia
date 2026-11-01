import type { ReactNode } from 'react'
import {
  ArrowRight,
  BookOpenCheck,
  Building2,
  ClipboardCheck,
  Database,
  FileDown,
  GraduationCap,
  History,
  LockKeyhole,
  Server,
  ServerCog,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { Anel } from '@/components/Anel'
import { BotaoLink } from '@/components/Botao'
import { CabecalhoPublico } from '@/components/CabecalhoPublico'
import { NomeProduto, SimboloLogo } from '@/components/Logo'
import { Mascote } from '@/features/auth/Mascote'
import { FundoLuzes } from '@/features/auth/MolduraAuth'

// As cinco dimensões do modelo de prontidão (backend/apps/questionarios/modelo_prontidao.py)
const DIMENSOES: { nome: string; descricao: string; icone: LucideIcon; exemplo: number }[] = [
  { nome: 'Tecnologia', descricao: 'Infraestrutura, integração e percepção da tecnologia de IA.', icone: Server, exemplo: 71.5 },
  { nome: 'Organização', descricao: 'Recursos, processos, cultura e colaboração entre as áreas.', icone: Building2, exemplo: 58.0 },
  { nome: 'Dados', descricao: 'Qualidade, governança e acesso aos dados da empresa.', icone: Database, exemplo: 44.5 },
  { nome: 'Conhecimento', descricao: 'Competências, capacitação e entendimento sobre IA.', icone: GraduationCap, exemplo: 62.0 },
  { nome: 'Estratégia', descricao: 'Liderança, oportunidades, plano e alinhamento da IA ao negócio.', icone: Target, exemplo: 50.5 },
]

const PASSOS: { titulo: string; texto: string }[] = [
  { titulo: 'Crie a conta da empresa', texto: 'Com e-mail e senha ou com a sua conta Google.' },
  {
    titulo: 'Responda ao questionário',
    texto: 'Afirmações e perguntas abertas sobre cada dimensão. O rascunho é salvo enquanto você responde.',
  },
  {
    titulo: 'Receba o resultado',
    texto: 'Nota geral e por dimensão, análise das respostas abertas e um plano de ação com recomendações.',
  },
  { titulo: 'Acompanhe a evolução', texto: 'Repita a avaliação e compare as rodadas no histórico.' },
]

const RECURSOS: { titulo: string; texto: string; icone: LucideIcon }[] = [
  {
    titulo: 'Plano de ação',
    texto: 'Recomendações do catálogo curado por especialistas, priorizadas pelas dimensões mais fracas.',
    icone: BookOpenCheck,
  },
  { titulo: 'Histórico e comparação', texto: 'Evolução do índice e de cada dimensão ao longo das avaliações.', icone: History },
  { titulo: 'Relatório em PDF', texto: 'O resultado completo em um arquivo para compartilhar com a equipe.', icone: FileDown },
]

const CONFIANCA: { titulo: string; texto: string; icone: LucideIcon }[] = [
  {
    titulo: 'Dados separados por empresa',
    texto: 'Cada empresa só acessa as próprias avaliações. Tentativas de abrir dados de outra empresa são bloqueadas e registradas.',
    icone: LockKeyhole,
  },
  {
    titulo: 'IA em infraestrutura própria',
    texto: 'A análise das respostas roda em um modelo local. Suas respostas não são enviadas a serviços externos de IA.',
    icone: ServerCog,
  },
]

/** Apresentação pública do produto, antes do login. Quem já entrou vê o atalho para o painel. */
export function PaginaInicial({ logado, destino }: { logado: boolean; destino: string }) {
  const acoes = logado ? (
    <BotaoLink to={destino} className="h-9 px-3">
      Ir para o painel
    </BotaoLink>
  ) : (
    <>
      <BotaoLink to="/login" variante="secundario" className="h-9 px-3">
        Entrar
      </BotaoLink>
      <BotaoLink to="/cadastro" className="h-9 px-3">
        Criar conta
      </BotaoLink>
    </>
  )

  return (
    <div className="relative isolate flex flex-1 flex-col bg-fundo">
      <FundoLuzes />
      <CabecalhoPublico acoes={acoes} />

      <main className="flex flex-col">
        <Heroi logado={logado} destino={destino} />

        <Secao
          id="dimensoes"
          sobretitulo="O que é avaliado"
          titulo="Cinco dimensões da prontidão para IA"
          descricao="O questionário cobre 19 fatores de prontidão, agrupados em cinco dimensões. Cada dimensão recebe uma nota de 0 a 100."
        >
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {DIMENSOES.map(({ nome, descricao, icone: Icone }) => (
              <li key={nome} className="cartao flex flex-col gap-3 p-5">
                <span className="grid size-10 place-items-center rounded-xl bg-destaque-fundo text-destaque">
                  <Icone size={20} aria-hidden />
                </span>
                <h3 className="text-base font-semibold text-titulo">{nome}</h3>
                <p className="text-sm">{descricao}</p>
              </li>
            ))}
          </ul>
        </Secao>

        <Secao id="como-funciona" sobretitulo="Como funciona" titulo="Da primeira resposta ao plano de ação">
          <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {PASSOS.map(({ titulo, texto }, i) => (
              <li key={titulo} className="flex flex-col gap-2 rounded-2xl border border-borda bg-superficie/70 p-5">
                <span
                  aria-hidden
                  className="grid size-8 place-items-center rounded-full bg-destaque text-sm font-semibold text-sobre-destaque tabular-nums"
                >
                  {i + 1}
                </span>
                <h3 className="text-base font-semibold text-titulo">{titulo}</h3>
                <p className="text-sm">{texto}</p>
              </li>
            ))}
          </ol>
          <ul className="mt-6 grid gap-4 md:grid-cols-3">
            {RECURSOS.map(({ titulo, texto, icone: Icone }) => (
              <li key={titulo} className="flex gap-3">
                <Icone size={20} aria-hidden className="mt-0.5 shrink-0 text-destaque" />
                <div className="flex flex-col gap-1">
                  <h3 className="text-sm font-semibold text-titulo">{titulo}</h3>
                  <p className="text-sm">{texto}</p>
                </div>
              </li>
            ))}
          </ul>
        </Secao>

        <Secao id="seguranca" sobretitulo="Segurança" titulo="Suas respostas ficam com a sua empresa">
          <ul className="grid gap-4 md:grid-cols-2">
            {CONFIANCA.map(({ titulo, texto, icone: Icone }) => (
              <li key={titulo} className="cartao flex gap-4 p-5 sm:p-6">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-destaque-fundo text-destaque">
                  <Icone size={20} aria-hidden />
                </span>
                <div className="flex flex-col gap-1">
                  <h3 className="text-base font-semibold text-titulo">{titulo}</h3>
                  <p className="text-sm">{texto}</p>
                </div>
              </li>
            ))}
          </ul>
        </Secao>

        {!logado && (
          <section aria-labelledby="chamada-final" className="px-4 pb-20 sm:px-10">
            <div className="mx-auto flex max-w-6xl flex-col items-start gap-5 rounded-3xl bg-destaque p-8 text-sobre-destaque sm:flex-row sm:items-center sm:justify-between sm:p-10">
              <div className="flex flex-col gap-2">
                <h2 id="chamada-final" className="text-2xl text-sobre-destaque">
                  Pronto para medir a prontidão da sua empresa?
                </h2>
                <p className="text-sm opacity-90">Crie a conta e comece a responder agora.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <BotaoLink to="/cadastro" variante="secundario" className="h-11 border-transparent px-5">
                  Criar conta
                </BotaoLink>
                <BotaoLink
                  to="/login"
                  className="h-11 border border-current/30 bg-transparent px-5 text-sobre-destaque shadow-none hover:bg-white/10"
                >
                  Já tenho conta
                </BotaoLink>
              </div>
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-borda px-4 py-8 sm:px-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-2.5">
            <SimboloLogo className="size-6" />
            <NomeProduto className="text-sm" />
          </span>
          <p className="text-sm">Avaliação de prontidão organizacional para adoção de inteligência artificial.</p>
        </div>
      </footer>
    </div>
  )
}

function Heroi({ logado, destino }: { logado: boolean; destino: string }) {
  return (
    <section aria-labelledby="titulo-principal" className="px-4 pt-8 pb-16 sm:px-10 sm:pt-14 lg:pb-24">
      <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="flex flex-col items-start gap-6 transition-[opacity,translate] duration-500 ease-saida starting:opacity-0 motion-safe:starting:translate-y-2">
          <p className="rounded-full border border-destaque/25 bg-destaque-fundo/70 px-3 py-1 text-xs font-medium text-destaque">
            Avaliação de prontidão organizacional
          </p>
          <h1 id="titulo-principal" className="text-4xl leading-[1.1] tracking-tight sm:text-5xl">
            Descubra o quanto sua empresa está pronta para adotar IA
          </h1>
          <p className="max-w-xl text-base sm:text-lg">
            Responda a um questionário sobre tecnologia, organização, dados, conhecimento e estratégia. Receba a nota de
            cada dimensão, a análise das suas respostas e um plano de ação com o que fazer primeiro.
          </p>
          <div className="flex w-full flex-col gap-3 min-[420px]:w-auto min-[420px]:flex-row">
            {logado ? (
              <BotaoLink to={destino} className="group h-12 px-6 text-base">
                Ir para o painel
                <ArrowRight size={18} aria-hidden className="transition-transform duration-150 ease-saida group-hover:translate-x-0.5" />
              </BotaoLink>
            ) : (
              <>
                <BotaoLink to="/cadastro" className="group h-12 px-6 text-base">
                  Criar conta
                  <ArrowRight size={18} aria-hidden className="transition-transform duration-150 ease-saida group-hover:translate-x-0.5" />
                </BotaoLink>
                <BotaoLink to="/login" variante="secundario" className="h-12 px-6 text-base">
                  Entrar
                </BotaoLink>
              </>
            )}
          </div>
          <a href="#como-funciona" className="text-sm font-medium text-destaque underline-offset-4 hover:underline">
            Ver como funciona
          </a>
        </div>

        <ExemploResultado />
      </div>
    </section>
  )
}

/** Ilustração do resultado com valores fictícios, marcada como exemplo. */
function ExemploResultado() {
  return (
    <figure className="relative mx-auto flex w-full max-w-md flex-col">
      <div className="relative z-10 -mb-3 hidden pl-2 sm:block">
        <Mascote estado="ocioso" />
      </div>
      <div className="cartao flex flex-col gap-5 p-6">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base">Resultado da avaliação</h2>
          <span className="rounded-full bg-suave px-2.5 py-0.5 text-xs font-medium">Exemplo</span>
        </div>
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center">
          <Anel valor={57.3} rotulo="índice geral" />
          <ul className="flex w-full flex-col gap-2.5" aria-label="Notas por dimensão no exemplo">
            {DIMENSOES.map(({ nome, exemplo }) => (
              <li key={nome} className="flex flex-col gap-1">
                <span className="flex justify-between text-xs">
                  <span className="font-medium text-titulo">{nome}</span>
                  <span className="tabular-nums">{exemplo.toFixed(1)}</span>
                </span>
                <span className="h-1.5 overflow-hidden rounded-full bg-suave" aria-hidden>
                  <span className="block h-full rounded-full bg-[var(--serie-atual)]" style={{ width: `${exemplo}%` }} />
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex items-start gap-3 rounded-xl bg-destaque-fundo/60 p-3 text-sm text-titulo">
          <ClipboardCheck size={18} aria-hidden className="mt-0.5 shrink-0 text-destaque" />
          <span>Primeira ação sugerida para a dimensão Dados, a de menor nota.</span>
        </div>
      </div>
      <figcaption className="sr-only">Exemplo ilustrativo de resultado, com notas fictícias.</figcaption>
    </figure>
  )
}

function Secao({
  id,
  sobretitulo,
  titulo,
  descricao,
  children,
}: {
  id: string
  sobretitulo: string
  titulo: string
  descricao?: string
  children: ReactNode
}) {
  return (
    <section id={id} aria-labelledby={`${id}-titulo`} className="scroll-mt-6 px-4 pb-20 sm:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex max-w-2xl flex-col gap-2">
          <p className="text-xs font-semibold tracking-wide text-destaque uppercase">{sobretitulo}</p>
          <h2 id={`${id}-titulo`} className="text-2xl tracking-tight sm:text-3xl">
            {titulo}
          </h2>
          {descricao && <p className="text-base">{descricao}</p>}
        </div>
        {children}
      </div>
    </section>
  )
}
