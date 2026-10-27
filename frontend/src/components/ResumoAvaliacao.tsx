import { Anel } from './Anel'
import { Delta } from './Delta'
import type { Avaliacao } from '@/features/avaliacoes/avaliacoesApi'

type Props = {
  avaliacao: Pick<Avaliacao, 'nota_geral' | 'delta_nota_geral' | 'nivel_maturidade'>
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
      <div className="relative flex w-full flex-col items-center gap-6 sm:flex-row sm:items-center sm:gap-10">
        <Anel valor={avaliacao.nota_geral} rotulo="de 100" className="size-52" />
        <div className="flex w-full flex-col gap-6">
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl">Índice geral de prontidão</h2>
            <p className="flex flex-wrap items-center gap-2 text-base">
              <Delta valor={avaliacao.delta_nota_geral} />
              {avaliacao.delta_nota_geral === null ? 'Primeira avaliação da empresa' : desde ? `desde ${desde}` : 'vs avaliação anterior'}
            </p>
          </div>

          <div>
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium tracking-wide uppercase">Nível de Prontidão</p>
              <div className="flex items-center gap-4">
                <div className="flex gap-1" aria-hidden>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <span
                      key={n}
                      className={`h-3 w-10 rounded-full ${n <= nivel ? 'bg-linear-to-r from-[#7c5ce6] to-[var(--serie-atual)]' : 'bg-suave'}`}
                    />
                  ))}
                </div>
                <span className="text-lg font-semibold whitespace-nowrap text-titulo">{nivel ? `${nivel} de 5` : '—'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
