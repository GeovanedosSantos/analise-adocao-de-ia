import type { ReactNode } from 'react'
import { CalendarClock, ChevronDown, Gauge, Target, TrendingUp } from 'lucide-react'
import { ROTULO_NIVEL, ROTULO_PRAZO, ROTULO_PRIORIDADE, type Recomendacao } from './catalogoApi'

type Props = {
  recomendacao: Pick<Recomendacao, 'titulo' | 'descricao' | 'prazo' | 'prioridade' | 'esforco' | 'impacto' | 'kpi'>
  /** Número da posição no plano de ação; sem ele, o cartão aparece como item do catálogo. */
  posicao?: number
  /** Linha extra acima do título (ex.: faixa de nota). */
  contexto?: ReactNode
}

/**
 * Uma recomendação: título e classificação sempre à vista; a ação e o KPI ao expandir (US06, UC06).
 * Usa o `<details>` nativo, que já é acessível por teclado e leitor de tela.
 */
export function CartaoRecomendacao({ recomendacao: r, posicao, contexto }: Props) {
  return (
    <details className="group rounded-xl border border-borda bg-superficie open:shadow-sm">
      <summary className="flex cursor-pointer list-none gap-4 rounded-xl p-4 focus-visible:outline-2 focus-visible:outline-destaque [&::-webkit-details-marker]:hidden">
        {posicao !== undefined && (
          <span
            aria-hidden
            className="grid size-8 shrink-0 place-items-center rounded-full bg-destaque-fundo text-sm font-semibold text-destaque"
          >
            {posicao}
          </span>
        )}
        <span className="flex min-w-0 flex-1 flex-col gap-2">
          {contexto && <span className="text-xs font-medium tracking-wide uppercase">{contexto}</span>}
          <span className="flex items-start justify-between gap-3">
            <span className="text-base font-medium text-titulo">
              {posicao !== undefined && <span className="sr-only">{posicao}. </span>}
              {r.titulo}
            </span>
            <ChevronDown
              size={18}
              aria-hidden
              className="mt-0.5 shrink-0 text-texto transition-transform duration-150 ease-saida group-open:rotate-180"
            />
          </span>
          <span className="flex flex-wrap gap-2">
            <Etiqueta icone={<CalendarClock size={12} aria-hidden />}>{ROTULO_PRAZO[r.prazo]}</Etiqueta>
            <Etiqueta destaque={r.prioridade === 'ALTO'}>Prioridade: {ROTULO_PRIORIDADE[r.prioridade]}</Etiqueta>
          </span>
        </span>
      </summary>
      <div className={`flex flex-col gap-2 px-4 pb-4 ${posicao !== undefined ? 'sm:pl-16' : ''}`}>
        <p className="text-sm leading-relaxed">{r.descricao}</p>
        {r.kpi && (
          <p className="flex items-start gap-1.5 text-sm">
            <Target size={14} aria-hidden className="mt-0.5 shrink-0 text-destaque" />
            <span>
              <span className="font-medium text-titulo">Como medir:</span> {r.kpi}
            </span>
          </p>
        )}
        <span className="flex flex-wrap gap-2 pt-1">
          <Etiqueta icone={<TrendingUp size={12} aria-hidden />}>Impacto: {ROTULO_NIVEL[r.impacto]}</Etiqueta>
          <Etiqueta icone={<Gauge size={12} aria-hidden />}>Esforço: {ROTULO_NIVEL[r.esforco]}</Etiqueta>
        </span>
      </div>
    </details>
  )
}

function Etiqueta({ icone, destaque = false, children }: { icone?: ReactNode; destaque?: boolean; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        destaque ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400' : 'bg-suave text-titulo'
      }`}
    >
      {icone}
      {children}
    </span>
  )
}
