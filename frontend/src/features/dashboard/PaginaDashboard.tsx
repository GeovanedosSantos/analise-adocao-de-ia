import { useEffect, useState, type ReactNode } from 'react'
import { Info, Sparkles, Target, TrendingDown, TrendingUp, type LucideIcon } from 'lucide-react'
import { ErroApi } from '@/api/cliente'
import { BotaoLink } from '@/components/Botao'
import { Delta } from '@/components/Delta'
import { Carregando, Cartao, MensagemPagina, Pagina } from '@/components/Pagina'
import { obterHistorico, type AvaliacaoHistorico } from '@/features/avaliacoes/avaliacoesApi'
import { ResumoAvaliacao } from '@/components/ResumoAvaliacao'
import { ExploradorDimensoes } from '@/features/avaliacoes/ExploradorDimensoes'
import { LinhaDoTempo, type PontoLinha, type SerieDimensao } from './graficos'

type Props = { aoExpirarSessao: () => void }

const PERIODOS = [
  ['6', '6 meses'],
  ['12', '12 meses'],
  ['tudo', 'Tudo'],
] as const
type Periodo = (typeof PERIODOS)[number][0]
const TOTAL_CORES = 8
const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium' })
const dataDe = (a: AvaliacaoHistorico) => formatoData.format(new Date(a.data_fim ?? a.data_inicio))

/** Tela inicial do usuário: indicadores de prontidão da empresa (UC04, US07, RF12 a RF14). */
export function PaginaDashboard({ aoExpirarSessao }: Props) {
  // Avaliações enviadas, com as pontuações, da mais recente para a mais antiga
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoHistorico[] | undefined>(undefined)
  const [erro, setErro] = useState<string | null>(null)
  const [periodo, setPeriodo] = useState<Periodo>('tudo')
  // Dimensões desligadas na linha do tempo (filtro por dimensão do UC04)
  const [ocultas, setOcultas] = useState<string[]>([])
  // Dimensão em destaque no explorador, no radar e na linha do tempo; null = a prioritária
  const [escolhida, setEscolhida] = useState<string | null>(null)
  // Fixado ao abrir a página: o filtro de período não muda a cada renderização
  const [agora] = useState(() => Date.now())

  useEffect(() => {
    let ativo = true
    async function carregar() {
      return (await obterHistorico()).filter((a) => a.status !== 'DRAFT')
    }
    carregar()
      .then((d) => ativo && setAvaliacoes(d))
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        else setErro('Não foi possível carregar os indicadores.')
      })
    return () => {
      ativo = false
    }
  }, [aoExpirarSessao])

  if (erro) return <MensagemPagina tipo="erro">{erro}</MensagemPagina>
  if (avaliacoes === undefined) return <Carregando />
  if (avaliacoes.length === 0) {
    return (
      <MensagemPagina titulo="Nenhuma avaliação ainda" acao={<BotaoLink to="/questionario">Responder questionário</BotaoLink>}>
        Responda o questionário para ver os indicadores de prontidão da sua empresa.
      </MensagemPagina>
    )
  }

  const [atual, anterior = null] = avaliacoes
  // Empate na menor nota: todas as empatadas são ponto de partida (US04)
  const prioritarias = atual.pontuacoes.filter((p) => p.prioritaria)
  const selecionada = escolhida ?? prioritarias[0]?.dimensao_codigo ?? atual.pontuacoes[0]?.dimensao_codigo ?? null

  // A cor segue a dimensão (ordem da avaliação atual, depois as que só existem nas antigas), não o filtro
  const todasDimensoes: SerieDimensao[] = []
  for (const p of avaliacoes.flatMap((a) => a.pontuacoes)) {
    if (todasDimensoes.some((d) => d.codigo === p.dimensao_codigo)) continue
    // shortcut: a partir da 9ª dimensão as cores se repetem; agrupar ou separar o gráfico se o questionário crescer
    const cor = `var(--dim-${(todasDimensoes.length % TOTAL_CORES) + 1})`
    todasDimensoes.push({ codigo: p.dimensao_codigo, nome: p.dimensao_nome, cor })
  }
  const corDe = (codigo: string) => todasDimensoes.find((d) => d.codigo === codigo)?.cor ?? 'var(--serie-atual)'

  const corte = periodo === 'tudo' ? -Infinity : new Date(agora).setMonth(new Date(agora).getMonth() - Number(periodo))
  const linha: PontoLinha[] = avaliacoes
    .filter((a) => a.nota_geral !== null)
    .map((a) => ({
      tempo: new Date(a.data_fim ?? a.data_inicio).getTime(),
      geral: a.nota_geral as number,
      ...Object.fromEntries(a.pontuacoes.map((p) => [p.dimensao_codigo, p.nota])),
    }))
    .filter((p) => p.tempo >= corte)
    .reverse()

  function alternarDimensao(codigo: string) {
    setOcultas((atuais) => (atuais.includes(codigo) ? atuais.filter((c) => c !== codigo) : [...atuais, codigo]))
  }

  return (
    <Pagina
      titulo="Dashboard"
      descricao={`Última avaliação em ${dataDe(atual)} · questionário v${atual.versao_questionario}`}
      acoes={
        <>
          <BotaoLink to={`/resultados/${atual.id}`} variante="secundario">
            Ver resultado completo
          </BotaoLink>
          <BotaoLink to="/questionario">Nova avaliação</BotaoLink>
        </>
      }
    >
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <ResumoAvaliacao avaliacao={atual} desde={anterior && dataDe(anterior)} className="xl:col-span-2" />
        <DestaquesDaAda atual={atual} anterior={anterior} aoSelecionar={setEscolhida} />
      </div>

      <Cartao titulo="Dimensões" descricao="Clique em uma dimensão para destacá-la no radar e na evolução.">
        <ExploradorDimensoes
          pontuacoes={atual.pontuacoes}
          corDe={corDe}
          selecionada={selecionada}
          aoSelecionar={setEscolhida}
          rotuloAnterior={anterior ? `Anterior (${dataDe(anterior)})` : undefined}
        />
      </Cartao>

      <Cartao
        titulo="Evolução ao longo do tempo"
        descricao="Índice geral e notas por dimensão em cada avaliação"
        acao={
          <div role="group" aria-label="Período" className="flex rounded-lg bg-suave p-1">
            {PERIODOS.map(([valor, rotulo]) => (
              <button
                key={valor}
                type="button"
                onClick={() => setPeriodo(valor)}
                aria-pressed={periodo === valor}
                className={`rounded-md px-3 py-1 text-sm font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-destaque ${
                  periodo === valor ? 'bg-superficie text-titulo shadow-sm' : 'text-texto hover:text-titulo'
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>
        }
      >
        {/* Chips: ligam e desligam cada dimensão; servem também de legenda */}
        <div role="group" aria-label="Dimensões no gráfico" className="flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-borda px-3 py-1 text-xs font-medium text-titulo">
            <span aria-hidden className="h-2.5 w-4 rounded-sm bg-[var(--serie-atual)] opacity-60" />
            Índice geral
          </span>
          {todasDimensoes.map((d) => {
            const ligada = !ocultas.includes(d.codigo)
            return (
              <button
                key={d.codigo}
                type="button"
                onClick={() => alternarDimensao(d.codigo)}
                aria-pressed={ligada}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-[background-color,border-color,opacity,transform] duration-150 ease-saida focus-visible:outline-2 focus-visible:outline-destaque active:scale-[0.96] ${
                  ligada ? 'border-borda bg-superficie text-titulo' : 'border-dashed border-borda text-texto opacity-60'
                } ${d.codigo === selecionada ? 'ring-2 ring-destaque/40' : ''}`}
              >
                <span aria-hidden className="size-2.5 rounded-full" style={{ background: ligada ? d.cor : 'var(--border)' }} />
                {d.nome}
              </button>
            )
          })}
        </div>

        {linha.length >= 2 ? (
          <>
            <LinhaDoTempo dados={linha} dimensoes={todasDimensoes.filter((d) => !ocultas.includes(d.codigo))} destaque={selecionada} />
            <BotaoLink to="/historico" variante="link" className="self-start">
              Ver os valores em tabela no histórico
            </BotaoLink>
          </>
        ) : (
          <p className="rounded-lg bg-suave px-4 py-8 text-center text-sm">
            {linha.length === 0
              ? 'Nenhuma avaliação neste período.'
              : 'Só uma avaliação neste período: a linha do tempo aparece a partir da segunda.'}
          </p>
        )}
      </Cartao>
    </Pagina>
  )
}

type Insight = { icone: LucideIcon; tom: 'bom' | 'ruim' | 'neutro'; texto: ReactNode; codigo?: string }

const TONS = {
  bom: 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-400',
  ruim: 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-400',
  neutro: 'bg-destaque-fundo text-destaque',
}

/** Frases curtas tiradas dos números da última avaliação; as que citam uma dimensão a destacam ao clicar. */
function DestaquesDaAda({
  atual,
  anterior,
  aoSelecionar,
}: {
  atual: AvaliacaoHistorico
  anterior: AvaliacaoHistorico | null
  aoSelecionar: (codigo: string) => void
}) {
  const comDelta = atual.pontuacoes.filter((p) => p.delta_percentual !== null)
  const ordenadas = [...comDelta].sort((a, b) => (b.delta_percentual ?? 0) - (a.delta_percentual ?? 0))
  const maior = ordenadas[0]
  const menor = ordenadas.length > 1 ? ordenadas[ordenadas.length - 1] : undefined
  const prioritarias = atual.pontuacoes.filter((p) => p.prioritaria)

  const itens: Insight[] = []
  if (!anterior) {
    itens.push({ icone: Info, tom: 'neutro', texto: 'Primeira avaliação: responda de novo em alguns meses para acompanhar a evolução.' })
  }
  if (maior && (maior.delta_percentual ?? 0) > 0) {
    itens.push({
      icone: TrendingUp,
      tom: 'bom',
      texto: (
        <>
          Maior avanço em <b className="text-titulo">{maior.dimensao_nome}</b>: <Delta valor={maior.delta_percentual} />
        </>
      ),
      codigo: maior.dimensao_codigo,
    })
  }
  if (menor) {
    const caiu = (menor.delta_percentual ?? 0) < 0
    itens.push({
      icone: TrendingDown,
      tom: caiu ? 'ruim' : 'neutro',
      texto: (
        <>
          {caiu ? 'Queda em ' : 'Menor avanço em '}
          <b className="text-titulo">{menor.dimensao_nome}</b>: <Delta valor={menor.delta_percentual} />
        </>
      ),
      codigo: menor.dimensao_codigo,
    })
  }
  if (prioritarias.length > 0) {
    itens.push({
      icone: Target,
      tom: 'neutro',
      texto: (
        <>
          Comece por <b className="text-titulo">{prioritarias.map((p) => p.dimensao_nome).join(' e ')}</b>, a menor nota.
        </>
      ),
      codigo: prioritarias[0].dimensao_codigo,
    })
  }

  return (
    <section className="cartao flex flex-col gap-4 p-6">
      <div className="flex items-center gap-2.5">
        <span className="grid size-8 place-items-center rounded-lg bg-linear-to-br from-[#4f7bf0] to-[#6d4fe0] text-white">
          <Sparkles size={16} aria-hidden />
        </span>
        <h2>Destaques da Ada</h2>
      </div>
      <ul className="flex flex-col gap-1">
        {itens.map((item, i) => {
          const conteudo = (
            <>
              <span className={`grid size-7 shrink-0 place-items-center rounded-md ${TONS[item.tom]}`}>
                <item.icone size={15} aria-hidden />
              </span>
              <span className="pt-0.5 text-sm leading-relaxed">{item.texto}</span>
            </>
          )
          return (
            <li key={i}>
              {item.codigo ? (
                <button
                  type="button"
                  onClick={() => aoSelecionar(item.codigo!)}
                  className="flex w-full items-start gap-3 rounded-lg p-2 text-left transition-colors duration-150 hover:bg-suave focus-visible:outline-2 focus-visible:outline-destaque"
                >
                  {conteudo}
                </button>
              ) : (
                <div className="flex items-start gap-3 p-2">{conteudo}</div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
