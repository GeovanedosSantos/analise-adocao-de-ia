import { useId } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

// Cores vêm dos tokens do index.css, que já trocam no tema escuro
const estiloTooltip = {
  contentStyle: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 12,
    fontSize: 13,
    boxShadow: '0 8px 24px -8px rgba(15,23,42,0.25)',
  },
  labelStyle: { color: 'var(--text-h)', fontWeight: 600, marginBottom: 4 },
  itemStyle: { color: 'var(--text-h)', padding: 0 },
}
const eixo = { stroke: 'var(--border)', tick: { fill: 'var(--text)', fontSize: 12 } }
const formatoNota = (v: unknown) => (typeof v === 'number' ? v.toFixed(1) : '—')

export type PontoRadar = { codigo: string; dimensao: string; atual: number; anterior?: number }

type PropsRadar = {
  dados: PontoRadar[]
  comAnterior: boolean
  selecionada: string | null
  aoSelecionar: (codigo: string) => void
}

/** Notas por dimensão da avaliação atual sobre a anterior (RF13). Clicar no nome de uma dimensão a seleciona. */
export function GraficoRadar({ dados, comAnterior, selecionada, aoSelecionar }: PropsRadar) {
  const codigoPorNome = new Map(dados.map((p) => [p.dimensao, p.codigo]))
  return (
    <ResponsiveContainer width="100%" height={340}>
      {/* Margem lateral: os nomes das dimensões ficam fora do raio e eram cortados no celular */}
      <RadarChart data={dados} outerRadius="70%" margin={{ top: 8, right: 40, bottom: 8, left: 40 }}>
        <PolarGrid stroke="var(--border)" />
        <PolarAngleAxis
          dataKey="dimensao"
          tick={(props: { x: number | string; y: number | string; textAnchor?: string; payload?: { value?: unknown } }) => {
            const nome = String(props.payload?.value ?? '')
            const codigo = codigoPorNome.get(nome) ?? ''
            const ativa = codigo === selecionada
            return (
              <text
                x={props.x}
                y={props.y}
                textAnchor={props.textAnchor as 'start' | 'middle' | 'end'}
                dominantBaseline="central"
                onClick={() => aoSelecionar(codigo)}
                className="cursor-pointer"
                fill={ativa ? 'var(--accent)' : 'var(--text)'}
                fontSize={ativa ? 13 : 12}
                fontWeight={ativa ? 700 : 500}
              >
                {nome}
              </text>
            )
          }}
        />
        {/* 60°: a escala fica entre dois eixos e não cobre o rótulo de uma dimensão */}
        <PolarRadiusAxis domain={[0, 100]} tickCount={5} angle={60} axisLine={false} tick={{ ...eixo.tick, fontSize: 10 }} />
        {comAnterior && (
          // Tracejada: a anterior se distingue da atual também sem depender da cor
          <Radar
            name="Anterior"
            dataKey="anterior"
            stroke="var(--serie-anterior)"
            strokeWidth={2}
            strokeDasharray="5 4"
            fill="var(--serie-anterior)"
            fillOpacity={0.06}
            isAnimationActive={false}
          />
        )}
        <Radar
          name="Atual"
          dataKey="atual"
          stroke="var(--serie-atual)"
          strokeWidth={2.5}
          fill="var(--serie-atual)"
          fillOpacity={0.18}
          isAnimationActive={false}
          // A dimensão selecionada ganha um ponto maior com anel
          dot={(p: { cx?: number; cy?: number; payload?: unknown }) => {
            const codigo = (p.payload as PontoRadar | undefined)?.codigo
            const ativa = codigo === selecionada
            return (
              <circle
                key={codigo}
                cx={p.cx}
                cy={p.cy}
                r={ativa ? 7 : 4}
                fill="var(--serie-atual)"
                stroke="var(--surface)"
                strokeWidth={ativa ? 3 : 2}
              />
            )
          }}
        />
        <Tooltip {...estiloTooltip} formatter={formatoNota} />
      </RadarChart>
    </ResponsiveContainer>
  )
}

/** Um ponto por avaliação: índice geral e a nota de cada dimensão, pelo código da dimensão. */
export type PontoLinha = { tempo: number; geral: number } & Record<string, number | undefined>
export type SerieDimensao = { codigo: string; nome: string; cor: string }

const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium' })
const formatoMes = new Intl.DateTimeFormat('pt-BR', { month: 'short', year: '2-digit' })

type PropsLinha = { dados: PontoLinha[]; dimensoes: SerieDimensao[]; destaque: string | null }

/**
 * Índice geral (área) e notas por dimensão (linhas) ao longo do tempo (RF14).
 * Eixo de tempo real: o espaço entre pontos reflete o intervalo entre avaliações.
 * Com uma dimensão em destaque, as outras linhas ficam apagadas.
 */
export function LinhaDoTempo({ dados, dimensoes, destaque }: PropsLinha) {
  const gradiente = useId()
  const algumaEmDestaque = destaque !== null && dimensoes.some((d) => d.codigo === destaque)
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={dados} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
        <defs>
          <linearGradient id={gradiente} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--serie-atual)" stopOpacity={0.28} />
            <stop offset="1" stopColor="var(--serie-atual)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="tempo"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          tickFormatter={(t: number) => formatoMes.format(t)}
          tickLine={false}
          {...eixo}
        />
        <YAxis domain={[0, 100]} tickCount={6} tickLine={false} axisLine={false} {...eixo} />
        <Tooltip
          {...estiloTooltip}
          cursor={{ stroke: 'var(--text)', strokeDasharray: '3 3' }}
          labelFormatter={(t) => formatoData.format(Number(t))}
          formatter={formatoNota}
        />
        {/* Índice geral como área: é o total, não mais uma dimensão */}
        <Area
          name="Índice geral"
          dataKey="geral"
          stroke="var(--serie-atual)"
          strokeWidth={2.5}
          fill={`url(#${gradiente})`}
          dot={{ r: 4, fill: 'var(--serie-atual)', stroke: 'var(--surface)', strokeWidth: 2 }}
          activeDot={{ r: 6, stroke: 'var(--surface)', strokeWidth: 2 }}
          isAnimationActive={false}
        />
        {dimensoes.map((d) => {
          const apagada = algumaEmDestaque && d.codigo !== destaque
          return (
            <Line
              key={d.codigo}
              name={d.nome}
              dataKey={d.codigo}
              stroke={d.cor}
              strokeWidth={d.codigo === destaque ? 3 : 1.75}
              strokeOpacity={apagada ? 0.2 : 1}
              dot={apagada ? false : { r: 3, fill: d.cor, stroke: 'var(--surface)', strokeWidth: 1.5 }}
              activeDot={{ r: 5, stroke: 'var(--surface)', strokeWidth: 2 }}
              // Dimensão ausente numa versão do questionário: a linha liga as avaliações em que ela existe
              connectNulls
              isAnimationActive={false}
            />
          )
        })}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
