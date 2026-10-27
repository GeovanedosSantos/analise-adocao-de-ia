import type { CSSProperties } from 'react'

const RAIO = 52
const CIRCUNFERENCIA = 2 * Math.PI * RAIO

/** Anel de progresso de 0 a 100 com o valor no centro. Preenche uma vez ao aparecer (só no primeiro render). */
export function Anel({ valor, rotulo, className = 'size-36' }: { valor: number | null; rotulo: string; className?: string }) {
  const fracao = Math.min(Math.max(valor ?? 0, 0), 100) / 100
  return (
    <div className={`relative grid shrink-0 ${className} place-items-center`}>
      <svg viewBox="0 0 120 120" className="absolute inset-0 -rotate-90" aria-hidden>
        <circle cx="60" cy="60" r={RAIO} fill="none" stroke="var(--muted)" strokeWidth={10} />
        <circle
          cx="60"
          cy="60"
          r={RAIO}
          fill="none"
          stroke="url(#anel-gradiente)"
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={CIRCUNFERENCIA}
          style={{ strokeDashoffset: CIRCUNFERENCIA * (1 - fracao), '--vazio': CIRCUNFERENCIA } as CSSProperties}
          // Começa vazio e enche em 700 ms ease-out; sem animação se o sistema pedir menos movimento
          className="transition-[stroke-dashoffset] duration-700 ease-saida motion-safe:starting:[stroke-dashoffset:var(--vazio)]"
        />
        <defs>
          <linearGradient id="anel-gradiente" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7c5ce6" />
            <stop offset="1" stopColor="var(--serie-atual)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="flex flex-col items-center">
        <span className="text-5xl font-bold tracking-tight text-titulo tabular-nums">{valor?.toFixed(1) ?? '—'}</span>
        <span className="text-sm">{rotulo}</span>
      </div>
    </div>
  )
}
