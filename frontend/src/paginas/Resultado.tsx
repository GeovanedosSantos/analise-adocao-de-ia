import { useEffect, useState } from 'react'
import { consultarStatus, obterAvaliacao, type Avaliacao } from '../api/avaliacoes'

const INTERVALO_POLLING_MS = 3000

export function Resultado({ avaliacao: inicial }: { avaliacao: Avaliacao }) {
  const [avaliacao, setAvaliacao] = useState(inicial)
  const processando = avaliacao.status === 'PROCESSANDO_IA'

  // A análise das respostas abertas roda no Celery: consulta o status até terminar (RNF06)
  useEffect(() => {
    if (!processando) return
    const timer = setInterval(async () => {
      try {
        const { status } = await consultarStatus(avaliacao.id)
        if (status !== 'PROCESSANDO_IA') setAvaliacao(await obterAvaliacao(avaliacao.id))
      } catch {
        // Falha pontual de rede: tenta no próximo ciclo
      }
    }, INTERVALO_POLLING_MS)
    return () => clearInterval(timer)
  }, [avaliacao.id, processando])

  const analises = avaliacao.respostas.filter((r) => r.feedback_ia)

  return (
    <div className="flex flex-col gap-6 p-6">
      <h2>Resultado da avaliação</h2>
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Indicador rotulo="Índice geral" valor={avaliacao.nota_geral?.toFixed(1) ?? '—'} />
        <Indicador rotulo="Nível de maturidade" valor={avaliacao.nivel_maturidade ? `${avaliacao.nivel_maturidade} de 5` : '—'} />
        <Indicador rotulo="Situação" valor={avaliacao.apta ? 'Apta' : 'Não apta'} />
      </dl>

      <section className="flex flex-col gap-2">
        <h2>Por dimensão</h2>
        {avaliacao.pontuacoes.map((p) => (
          <p key={p.dimensao} className={p.prioritaria ? 'font-medium text-destaque' : ''}>
            {p.dimensao_nome}: {p.nota.toFixed(1)}
            {p.prioritaria && ' · ponto de partida recomendado'}
          </p>
        ))}
      </section>

      {processando && <p aria-live="polite">A IA está analisando as respostas abertas…</p>}
      {avaliacao.status === 'ERRO_PROCESSAMENTO' && (
        <p role="alert" className="text-red-600">
          Não foi possível analisar as respostas abertas. As notas acima continuam válidas.
        </p>
      )}
      {analises.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2>Análise das respostas abertas</h2>
          {analises.map((r) => (
            <p key={r.pergunta}>{r.feedback_ia?.analise_qualitativa}</p>
          ))}
        </section>
      )}
    </div>
  )
}

function Indicador({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="rounded border border-borda p-4">
      <dt className="text-sm">{rotulo}</dt>
      <dd className="text-2xl font-medium text-titulo">{valor}</dd>
    </div>
  )
}
