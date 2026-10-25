import { useEffect, useState } from 'react'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao } from '@/components/Botao'
import { acompanharProcessamento } from './acompanhamento'
import { consultarStatus, obterAvaliacao, type Avaliacao } from './avaliacoesApi'

type Props = {
  avaliacao: Avaliacao
  /** Veio direto do envio do questionário: mostra a mensagem de conclusão. */
  enviada?: boolean
  aoExpirarSessao: () => void
}

export function Resultado({ avaliacao: inicial, enviada = false, aoExpirarSessao }: Props) {
  const [avaliacao, setAvaliacao] = useState(inicial)
  const [esgotado, setEsgotado] = useState(false)
  const [rodada, setRodada] = useState(0)
  const processando = avaliacao.status === 'PROCESSANDO_IA'

  // A análise das respostas abertas roda no Celery: consulta o status até terminar ou até o limite
  useEffect(() => {
    if (!processando) return
    return acompanharProcessamento(
      async () => {
        const { status } = await consultarStatus(avaliacao.id)
        return status === 'PROCESSANDO_IA' ? null : obterAvaliacao(avaliacao.id)
      },
      { aoTerminar: setAvaliacao, aoEsgotar: () => setEsgotado(true), aoFalhar: aoExpirarSessao },
      { ehDefinitivo: (erro) => erro instanceof ErroApi && erro.status === 401 },
    )
  }, [avaliacao.id, processando, rodada, aoExpirarSessao])

  function verificarDeNovo() {
    setEsgotado(false)
    setRodada((r) => r + 1)
  }

  const analises = avaliacao.respostas.filter((r) => r.feedback_ia)

  return (
    <div className="flex flex-col gap-6 p-6">
      {enviada && (
        <Alerta tipo="sucesso" titulo="Avaliação enviada">
          Suas respostas foram registradas e a pontuação já está calculada.
        </Alerta>
      )}
      <h2>Resultado da avaliação</h2>
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Indicador rotulo="Índice geral" valor={avaliacao.nota_geral?.toFixed(1) ?? '—'} />
        <Indicador rotulo="Nível de maturidade" valor={avaliacao.nivel_maturidade ? `${avaliacao.nivel_maturidade} de 5` : '—'} />
        <Indicador rotulo="Situação" valor={avaliacao.apta ? 'Apta' : 'Não apta'} />
      </dl>

      <section className="flex flex-col gap-2 rounded-xl border border-borda bg-superficie p-6">
        <h2>Por dimensão</h2>
        {avaliacao.pontuacoes.map((p) => (
          <p key={p.dimensao} className={p.prioritaria ? 'font-medium text-destaque' : ''}>
            {p.dimensao_nome}: {p.nota.toFixed(1)}
            {p.prioritaria && ' · ponto de partida recomendado'}
          </p>
        ))}
      </section>

      {processando && !esgotado && <Alerta>A IA está analisando as respostas abertas…</Alerta>}
      {processando && esgotado && (
        <Alerta
          tipo="aviso"
          titulo="A análise está demorando"
          acao={<Botao variante="secundario" onClick={verificarDeNovo}>Verificar de novo</Botao>}
        >
          A IA está levando mais tempo que o normal para analisar as respostas abertas. As notas acima já são válidas;
          verifique de novo agora ou mais tarde.
        </Alerta>
      )}
      {avaliacao.status === 'ERRO_PROCESSAMENTO' && (
        <Alerta tipo="aviso" titulo="Análise das respostas abertas indisponível">
          Não foi possível analisar as respostas abertas. As notas acima continuam válidas.
        </Alerta>
      )}
      {analises.length > 0 && (
        <section className="flex flex-col gap-2 rounded-xl border border-borda bg-superficie p-6">
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
    <div className="rounded-xl border border-borda bg-superficie p-4">
      <dt className="text-sm">{rotulo}</dt>
      <dd className="text-2xl font-medium text-titulo">{valor}</dd>
    </div>
  )
}
