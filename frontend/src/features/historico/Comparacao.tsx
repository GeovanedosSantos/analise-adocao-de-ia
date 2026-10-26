import { useEffect, useState } from 'react'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Delta } from '@/components/Delta'
import { Cartao } from '@/components/Pagina'
import { obterAvaliacao, type Avaliacao } from '@/features/avaliacoes/avaliacoesApi'

/** `ids` da avaliação mais antiga para a mais recente. */
type Props = { ids: string[]; aoExpirarSessao: () => void }

const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' })

/** Notas por dimensão de duas ou mais avaliações lado a lado (UC05). */
export function Comparacao({ ids, aoExpirarSessao }: Props) {
  const [avaliacoes, setAvaliacoes] = useState<Avaliacao[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  // shortcut: busca o detalhe de cada avaliação; trocar pelo endpoint de histórico (RF11) quando existir
  // Depende da lista em texto: o array chega novo a cada renderização da página
  const chave = ids.join()
  useEffect(() => {
    let ativo = true
    Promise.all(chave.split(',').map((id) => obterAvaliacao(id)))
      .then((dados) => ativo && setAvaliacoes(dados))
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        else setErro('Não foi possível carregar a comparação.')
      })
    return () => {
      ativo = false
    }
  }, [chave, aoExpirarSessao])

  if (erro) return <Alerta tipo="erro">{erro}</Alerta>
  if (!avaliacoes) return <p>Carregando comparação…</p>

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
