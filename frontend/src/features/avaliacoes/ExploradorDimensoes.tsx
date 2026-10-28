import type { ReactNode } from 'react'
import { Delta } from '@/components/Delta'
import { GraficoRadar, type PontoRadar } from '@/features/dashboard/graficos'
import type { Pontuacao } from './avaliacoesApi'

type Props = {
  pontuacoes: Pontuacao[]
  corDe: (codigo: string) => string
  selecionada: string | null
  aoSelecionar: (codigo: string) => void
  /** Rótulo da série anterior no radar (ex.: "Anterior (1 de jun. de 2026)"). */
  rotuloAnterior?: string
}

const notaAnterior = (p: Pontuacao) => p.nota_anterior ?? undefined

/**
 * Lista clicável das dimensões (barra de 0 a 100 com traço na nota anterior) ao lado do radar.
 * A dimensão escolhida fica em destaque nos dois; clicar no nome dela no radar também escolhe.
 */
export function ExploradorDimensoes({ pontuacoes, corDe, selecionada, aoSelecionar, rotuloAnterior = 'Anterior' }: Props) {
  const radar: PontoRadar[] = pontuacoes.map((p) => ({
    codigo: p.dimensao_codigo,
    dimensao: p.dimensao_nome,
    atual: p.nota,
    anterior: notaAnterior(p),
  }))
  const comAnterior = radar.some((p) => p.anterior !== undefined)
  const escolhida = pontuacoes.find((p) => p.dimensao_codigo === selecionada)

  return (
    <div className="grid grid-cols-1 items-center gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <div className="flex flex-col gap-4">
      <ul className="flex flex-col gap-1.5">
        {pontuacoes.map((p) => {
          const ativa = p.dimensao_codigo === selecionada
          const anterior = notaAnterior(p)
          return (
            <li key={p.dimensao}>
              <button
                type="button"
                onClick={() => aoSelecionar(p.dimensao_codigo)}
                aria-pressed={ativa}
                className={`selecionavel flex w-full flex-col gap-2 rounded-xl border px-3.5 py-3 text-left transition-[background-color,border-color,translate] duration-150 ease-saida focus-visible:outline-2 focus-visible:outline-destaque active:scale-[0.99] ${
                  ativa
                    ? 'border-destaque/40 bg-destaque-fundo/60 shadow-sm'
                    : 'border-transparent hover:translate-x-1 hover:bg-suave'
                }`}
              >
                <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span aria-hidden className="size-2.5 shrink-0 rounded-full" style={{ background: corDe(p.dimensao_codigo) }} />
                  <span className="font-medium text-titulo">{p.dimensao_nome}</span>
                  {p.prioritaria && (
                    <span className="rounded-full bg-destaque px-2 py-0.5 text-[11px] font-semibold text-sobre-destaque">
                      Ponto de partida
                    </span>
                  )}
                  <span className="ml-auto flex items-center gap-2">
                    <Delta valor={p.delta_percentual} />
                    <span className="w-10 text-right font-semibold text-titulo tabular-nums">{p.nota.toFixed(1)}</span>
                  </span>
                </span>
                {/* Barra de 0 a 100 com um traço na nota anterior */}
                <span aria-hidden className="relative block h-1.5 rounded-full bg-suave">
                  <span
                    className="absolute inset-y-0 left-0 rounded-full"
                    style={{ width: `${Math.min(Math.max(p.nota, 0), 100)}%`, background: corDe(p.dimensao_codigo) }}
                  />
                  {anterior !== undefined && (
                    <span
                      className="absolute -top-1 -bottom-1 w-0.5 rounded-full bg-titulo/60"
                      style={{ left: `${Math.min(Math.max(anterior, 0), 100)}%` }}
                    />
                  )}
                </span>
                {anterior !== undefined && <span className="sr-only">Nota anterior: {anterior.toFixed(1)}</span>}
              </button>
            </li>
          )
        })}
      </ul>
      {escolhida && escolhida.fatores.length > 0 && (
        <div className="flex flex-col gap-2 px-1">
          <p className="text-sm">
            Fatores avaliados em <span className="font-medium text-titulo">{escolhida.dimensao_nome}</span>
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {escolhida.fatores.map((fator) => (
              <li key={fator} className="rounded-full bg-suave px-2.5 py-1 text-xs font-medium text-titulo">
                {fator}
              </li>
            ))}
          </ul>
        </div>
      )}
      </div>

      <div className="flex flex-col gap-2">
        <GraficoRadar dados={radar} comAnterior={comAnterior} selecionada={selecionada} aoSelecionar={aoSelecionar} />
        <div className="flex justify-center gap-5 text-xs">
          <Legenda cor="var(--serie-atual)">Atual</Legenda>
          {comAnterior && (
            <Legenda cor="var(--serie-anterior)" tracejada>
              {rotuloAnterior}
            </Legenda>
          )}
        </div>
      </div>
    </div>
  )
}

function Legenda({ cor, tracejada = false, children }: { cor: string; tracejada?: boolean; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-titulo">
      <svg width="18" height="6" aria-hidden>
        <line x1="1" y1="3" x2="17" y2="3" stroke={cor} strokeWidth={2.5} strokeDasharray={tracejada ? '4 3' : undefined} strokeLinecap="round" />
      </svg>
      {children}
    </span>
  )
}
