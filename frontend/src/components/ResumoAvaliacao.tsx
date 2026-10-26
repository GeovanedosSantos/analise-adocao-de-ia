import { Anel } from './Anel'
import { Delta } from './Delta'
import type { Avaliacao } from '@/features/avaliacoes/avaliacoesApi'

type Props = {
  avaliacao: Pick<Avaliacao, 'nota_geral' | 'delta_nota_geral' | 'nivel_maturidade' | 'apta'>
  /** Data da avaliação anterior, para "desde …"; sem ela, mostra que é a primeira. */
  desde?: string | null
  className?: string
}

/** Cartão principal de uma avaliação: anel do índice geral, variação, nível em degraus e situação. */
export function ResumoAvaliacao({ avaliacao, desde, className = '' }: Props) {
  const nivel = avaliacao.nivel_maturidade ?? 0
  return (
    <section className={`cartao flex items-center overflow-hidden p-6 ${className}`}>
      {/* Brilho decorativo no canto */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-24 size-72 rounded-full bg-[radial-gradient(circle,rgba(124,92,230,0.18),transparent_65%)]"
      />
      <div className="relative flex w-full flex-col items-center gap-6 sm:flex-row sm:items-center sm:gap-8">
        <Anel valor={avaliacao.nota_geral} rotulo="de 100" />
        <div className="flex w-full flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2>Índice geral de prontidão</h2>
            <p className="flex flex-wrap items-center gap-2 text-sm">
              <Delta valor={avaliacao.delta_nota_geral} />
              {avaliacao.delta_nota_geral === null ? 'Primeira avaliação da empresa' : desde ? `desde ${desde}` : 'vs avaliação anterior'}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <p className="text-xs font-medium tracking-wide uppercase">Nível de maturidade</p>
              <div className="flex items-center gap-3">
                <div className="flex gap-1" aria-hidden>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <span
                      key={n}
                      className={`h-2 w-6 rounded-full ${n <= nivel ? 'bg-linear-to-r from-[#7c5ce6] to-[var(--serie-atual)]' : 'bg-suave'}`}
                    />
                  ))}
                </div>
                <span className="font-semibold text-titulo">{nivel ? `${nivel} de 5` : '—'}</span>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-xs font-medium tracking-wide uppercase">Situação</p>
              <span
                className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-semibold ${
                  avaliacao.apta
                    ? 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-400'
                    : 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
                }`}
              >
                <span aria-hidden className="size-1.5 rounded-full bg-current" />
                {avaliacao.apta ? 'Apta para iniciar a adoção' : 'Ainda não apta'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
