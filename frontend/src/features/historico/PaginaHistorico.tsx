import { useEffect, useState } from 'react'
import { ErroApi } from '@/api/cliente'
import { Botao, BotaoLink } from '@/components/Botao'
import { Delta } from '@/components/Delta'
import { Indicador } from '@/components/Indicador'
import { Carregando, Cartao, MensagemPagina, Pagina } from '@/components/Pagina'
import { obterHistorico, type AvaliacaoHistorico } from '@/features/avaliacoes/avaliacoesApi'
import { Comparacao } from './Comparacao'

type Props = { aoExpirarSessao: () => void }

const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' })

/** Avaliações enviadas pela empresa, com link para o resultado e comparação entre duas (UC05, RF11). */
export function PaginaHistorico({ aoExpirarSessao }: Props) {
  const [avaliacoes, setAvaliacoes] = useState<AvaliacaoHistorico[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [selecionadas, setSelecionadas] = useState<string[]>([])

  useEffect(() => {
    let ativo = true
    obterHistorico()
      .then((dados) => {
        // O rascunho ainda não tem resultado para mostrar nem comparar
        if (ativo) setAvaliacoes(dados.filter((a) => a.status !== 'DRAFT'))
      })
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        else setErro('Não foi possível carregar o histórico.')
      })
    return () => {
      ativo = false
    }
  }, [aoExpirarSessao])

  function alternar(id: string) {
    setSelecionadas((atual) => (atual.includes(id) ? atual.filter((s) => s !== id) : [...atual, id]))
  }

  if (erro) return <MensagemPagina tipo="erro">{erro}</MensagemPagina>
  if (!avaliacoes) return <Carregando />
  if (avaliacoes.length === 0) {
    return (
      <MensagemPagina titulo="Nenhuma avaliação enviada" acao={<BotaoLink to="/questionario">Responder questionário</BotaoLink>}>
        O histórico aparece depois do primeiro envio do questionário.
      </MensagemPagina>
    )
  }

  // A comparação vai da mais antiga (à esquerda) à mais recente, seja qual for a ordem de marcação
  const avaliacoesComparadas = avaliacoes.filter((a) => selecionadas.includes(a.id)).reverse()

  // Resumo do histórico: notas em ordem cronológica (a listagem vem da mais recente)
  const comNota = avaliacoes.filter((a) => a.nota_geral !== null).reverse()
  const notas = comNota.map((a) => a.nota_geral as number)
  const melhor = comNota.reduce<AvaliacaoHistorico | null>((m, a) => (!m || (a.nota_geral ?? 0) > (m.nota_geral ?? 0) ? a : m), null)
  const evolucao = notas.length >= 2 ? notas[notas.length - 1] - notas[0] : null
  const dataDe = (a: AvaliacaoHistorico) => formatoData.format(new Date(a.data_fim ?? a.data_inicio))

  return (
    <Pagina titulo="Histórico" descricao="Todas as avaliações enviadas pela empresa, da mais recente para a mais antiga.">
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Indicador
          rotulo="Avaliações enviadas"
          valor={String(avaliacoes.length)}
          rodape={comNota.length ? `desde ${dataDe(comNota[0])}` : undefined}
        />
        <Indicador
          rotulo="Melhor índice geral"
          valor={melhor?.nota_geral?.toFixed(1) ?? '—'}
          rodape={melhor ? `em ${dataDe(melhor)}` : undefined}
        />
        <Indicador
          rotulo="Evolução total"
          valor={evolucao === null ? '—' : `${evolucao > 0 ? '+' : ''}${evolucao.toFixed(1).replace('.', ',')} pts`}
          rodape="da primeira para a última avaliação"
          serie={notas}
        />
      </dl>

      <Cartao
        titulo="Avaliações"
        descricao="Clique nas linhas para marcar duas ou mais e comparar as notas por dimensão."
        acao={
          selecionadas.length > 0 && (
            <Botao variante="secundario" onClick={() => setSelecionadas([])}>
              Limpar seleção ({selecionadas.length})
            </Botao>
          )
        }
      >
        {/* relative: prende os textos sr-only (absolutos) dentro da rolagem, sem alargar a página no celular */}
        <div className="relative overflow-x-auto">
          <table className="tabela">
            <thead>
              <tr>
                <th className="w-10 pl-2">
                  <span className="sr-only">Comparar</span>
                </th>
                <th>Data</th>
                <th>Versão</th>
                <th>Índice geral</th>
                <th>Nível</th>
                <th>Situação</th>
                <th className="pr-0">
                  <span className="sr-only">Resultado</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {avaliacoes.map((a) => {
                const data = formatoData.format(new Date(a.data_fim ?? a.data_inicio))
                const marcada = selecionadas.includes(a.id)
                return (
                  <tr
                    key={a.id}
                    // A linha inteira marca/desmarca (atalho do mouse); o checkbox continua sendo o controle acessível
                    onClick={(e) => {
                      if (!(e.target as Element).closest('a, input')) alternar(a.id)
                    }}
                    className={`selecionavel cursor-pointer transition-colors duration-150 ${
                      marcada ? 'bg-destaque-fundo/50' : 'hover:bg-suave/70'
                    }`}
                  >
                    <td className="pl-2">
                      <input
                        type="checkbox"
                        checked={marcada}
                        onChange={() => alternar(a.id)}
                        aria-label={`Comparar a avaliação de ${data}`}
                        className="size-4 align-middle"
                      />
                    </td>
                    <td className="whitespace-nowrap text-titulo">{data}</td>
                    <td>v{a.versao_questionario}</td>
                    <td className="whitespace-nowrap">
                      <span className="mr-2 font-semibold text-titulo">{a.nota_geral?.toFixed(1) ?? '—'}</span>
                      <Delta valor={a.delta_nota_geral} />
                    </td>
                    <td className="whitespace-nowrap">{a.nivel_prontidao ? `${a.nivel_prontidao} de 5` : '—'}</td>
                    <td className="whitespace-nowrap">
                      <Situacao apta={a.apta} />
                    </td>
                    <td className="pr-0 text-right whitespace-nowrap">
                      <BotaoLink to={`/resultados/${a.id}`} variante="link">
                        Ver resultado
                      </BotaoLink>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Cartao>

      {avaliacoesComparadas.length >= 2 && (
        <Comparacao key={avaliacoesComparadas.map((a) => a.id).join()} avaliacoes={avaliacoesComparadas} />
      )}
    </Pagina>
  )
}

function Situacao({ apta }: { apta: boolean | null }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
        apta ? 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-400' : 'bg-suave text-texto'
      }`}
    >
      <span aria-hidden className={`size-1.5 rounded-full ${apta ? 'bg-current' : 'bg-texto'}`} />
      {apta ? 'Apta' : 'Não apta'}
    </span>
  )
}
