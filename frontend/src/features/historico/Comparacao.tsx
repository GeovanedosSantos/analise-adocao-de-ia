import { Delta } from '@/components/Delta'
import { Cartao } from '@/components/Pagina'
import type { AvaliacaoHistorico } from '@/features/avaliacoes/avaliacoesApi'

/** Avaliações da mais antiga para a mais recente. */
type Props = { avaliacoes: AvaliacaoHistorico[] }

const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' })

/** Notas por dimensão de duas ou mais avaliações lado a lado (UC05). */
export function Comparacao({ avaliacoes }: Props) {
  // Casa as dimensões pelo código: entre versões do questionário o id muda, o código não
  const dimensoes = new Map<string, string>()
  for (const p of [...avaliacoes].reverse().flatMap((a) => a.pontuacoes)) {
    if (!dimensoes.has(p.dimensao_codigo)) dimensoes.set(p.dimensao_codigo, p.dimensao_nome)
  }
  const linhas = [...dimensoes].map(([codigo, nome]) => ({
    codigo,
    nome,
    notas: avaliacoes.map((a) => a.pontuacoes.find((p) => p.dimensao_codigo === codigo)?.nota),
  }))

  return (
    <Cartao titulo="Comparação" descricao="Da mais antiga para a mais recente selecionada">
      <div className="relative overflow-x-auto">
        <table className="tabela">
          <thead>
            <tr>
              <th>Dimensão</th>
              {avaliacoes.map((a) => (
                <th key={a.id}>{formatoData.format(new Date(a.data_fim ?? a.data_inicio))}</th>
              ))}
              <th className="pr-0">Diferença</th>
            </tr>
          </thead>
          <tbody>
            <Linha nome="Índice geral" notas={avaliacoes.map((a) => a.nota_geral)} destaque />
            {linhas.map((l) => (
              <Linha key={l.codigo} nome={l.nome} notas={l.notas} />
            ))}
          </tbody>
        </table>
      </div>
    </Cartao>
  )
}

type PropsLinha = { nome: string; notas: (number | null | undefined)[]; destaque?: boolean }

function Linha({ nome, notas, destaque = false }: PropsLinha) {
  // Diferença entre a primeira e a última avaliação em que a dimensão aparece
  const presentes = notas.filter((n): n is number => n != null)
  const diferenca = presentes.length >= 2 ? presentes[presentes.length - 1] - presentes[0] : null
  return (
    <tr className={destaque ? 'bg-suave/60 font-semibold text-titulo' : ''}>
      <td>{nome}</td>
      {notas.map((n, i) => (
        <td key={i}>{n?.toFixed(1) ?? '—'}</td>
      ))}
      <td className="pr-0">{diferenca === null ? '—' : <Delta valor={diferenca} referencia="à mais antiga selecionada" />}</td>
    </tr>
  )
}
