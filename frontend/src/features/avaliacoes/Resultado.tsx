import { useEffect, useState } from 'react'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { ResumoAvaliacao } from '@/components/ResumoAvaliacao'
import { FileDown, Sparkles, ThumbsUp, TriangleAlert } from 'lucide-react'
import { Cartao, Pagina } from '@/components/Pagina'
import { acompanharProcessamento } from './acompanhamento'
import { ExploradorDimensoes } from './ExploradorDimensoes'
import { CartaoRecomendacao } from '@/features/catalogo/CartaoRecomendacao'
import { baixarPdf, consultarStatus, obterAvaliacao, type Avaliacao, type ItemPlano } from './avaliacoesApi'

const formatoData = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'long' })
const TOTAL_CORES = 8

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
  const [escolhida, setEscolhida] = useState<string | null>(null)
  const pdf = useExportarPdf(avaliacao.id, aoExpirarSessao)
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
  const data = formatoData.format(new Date(avaliacao.data_fim ?? avaliacao.data_inicio))
  // Começa pela dimensão prioritária, como no dashboard
  const selecionada =
    escolhida ?? avaliacao.pontuacoes.find((p) => p.prioritaria)?.dimensao_codigo ?? avaliacao.pontuacoes[0]?.dimensao_codigo ?? null
  // Cor fixa por dimensão, na ordem do questionário (mesma paleta da linha do tempo)
  const corDe = (codigo: string) =>
    `var(--dim-${(Math.max(avaliacao.pontuacoes.findIndex((p) => p.dimensao_codigo === codigo), 0) % TOTAL_CORES) + 1})`
  const grupos = agruparPorDimensao(avaliacao)

  return (
    <Pagina
      titulo="Resultado da avaliação"
      descricao={`Enviada em ${data} · questionário v${avaliacao.versao_questionario}`}
      acoes={
        <>
          <BotaoLink to="/historico" variante="secundario">
            Ver histórico
          </BotaoLink>
          <Botao onClick={pdf.exportar} disabled={pdf.gerando}>
            <FileDown size={16} aria-hidden />
            {pdf.gerando ? 'Gerando PDF…' : 'Exportar PDF'}
          </Botao>
        </>
      }
    >
      {pdf.erro && (
        <Alerta
          tipo="erro"
          titulo="PDF não gerado"
          acao={
            <Botao variante="secundario" onClick={pdf.exportar} disabled={pdf.gerando}>
              Tentar novamente
            </Botao>
          }
        >
          {pdf.erro}
        </Alerta>
      )}
      {enviada && (
        <Alerta tipo="sucesso" titulo="Avaliação enviada">
          Suas respostas foram registradas e a pontuação já está calculada.
        </Alerta>
      )}

      <ResumoAvaliacao avaliacao={avaliacao} />

      <Cartao titulo="Por dimensão" descricao="Clique em uma dimensão para destacá-la no radar. O traço marca a nota anterior.">
        <ExploradorDimensoes
          pontuacoes={avaliacao.pontuacoes}
          corDe={corDe}
          selecionada={selecionada}
          aoSelecionar={setEscolhida}
        />
      </Cartao>

      {processando && !esgotado && (
        <Alerta titulo="Análise em processamento">
          A IA está analisando as respostas abertas e priorizando o plano de ação. As notas e as recomendações abaixo
          já valem; a ordem é atualizada quando a análise terminar.
        </Alerta>
      )}
      {processando && esgotado && (
        <Alerta
          tipo="aviso"
          titulo="A análise está demorando"
          acao={<Botao variante="secundario" onClick={verificarDeNovo}>Verificar de novo</Botao>}
        >
          A IA está levando mais tempo que o normal. As notas e o plano de ação já são válidos; verifique de novo agora
          ou mais tarde.
        </Alerta>
      )}
      {avaliacao.status === 'ERRO_PROCESSAMENTO' && (
        <Alerta tipo="aviso" titulo="Erro de processamento">
          A IA não conseguiu concluir a análise. As notas continuam válidas e o plano de ação abaixo segue as faixas de
          pontuação, sem a priorização pelas respostas abertas.
        </Alerta>
      )}

      <Cartao
        titulo="Plano de ação"
        descricao={
          avaliacao.recomendacoes_ordenadas_ia
            ? 'Recomendações do catálogo para as notas desta avaliação, priorizadas pela IA a partir das respostas abertas.'
            : 'Recomendações do catálogo para as notas desta avaliação, começando pelas dimensões mais fracas.'
        }
      >
        {grupos.length === 0 ? (
          <p className="text-sm">Nenhuma recomendação do catálogo se aplica às notas desta avaliação.</p>
        ) : (
          <div className="flex flex-col gap-6">
            {grupos.map((grupo) => (
              <section key={grupo.codigo} className="flex flex-col gap-3">
                <h3 className="flex flex-wrap items-center gap-2 text-base">
                  <span aria-hidden className="size-2.5 rounded-full" style={{ background: corDe(grupo.codigo) }} />
                  {grupo.nome}
                  <span className="text-sm font-normal">· nota {Math.round(grupo.nota)}</span>
                  {grupo.prioritaria && (
                    <span className="rounded-full bg-destaque px-2 py-0.5 text-[11px] font-semibold text-sobre-destaque">
                      Ponto de partida
                    </span>
                  )}
                </h3>
                <ol className="flex flex-col gap-2">
                  {grupo.itens.map((r) => (
                    <li key={r.codigo}>
                      <CartaoRecomendacao recomendacao={r} posicao={r.posicao} />
                    </li>
                  ))}
                </ol>
              </section>
            ))}
          </div>
        )}
      </Cartao>

      {analises.length > 0 && (
        <section className="cartao flex flex-col gap-4 p-5 sm:p-6">
          <div className="flex items-center gap-2.5">
            <span className="grid size-8 place-items-center rounded-lg bg-linear-to-br from-[#4f7bf0] to-[#6d4fe0] text-white">
              <Sparkles size={16} aria-hidden />
            </span>
            <div className="flex flex-col">
              <h2>Análise da Ada</h2>
              <p className="text-sm">Leitura das respostas abertas, feita pela IA local, sem enviar o texto para fora</p>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {analises.map((r) => {
              const { analise_qualitativa, pontos_fortes, riscos } = r.feedback_ia!
              return (
                <article key={r.pergunta} className="flex flex-col gap-3 rounded-xl bg-suave/60 p-4">
                  <p className="leading-relaxed text-titulo">{analise_qualitativa}</p>
                  {(pontos_fortes.length > 0 || riscos.length > 0) && (
                    <div className="flex flex-wrap gap-2">
                      {pontos_fortes.map((t) => (
                        <Etiqueta key={t} tom="bom">
                          {t}
                        </Etiqueta>
                      ))}
                      {riscos.map((t) => (
                        <Etiqueta key={t} tom="risco">
                          {t}
                        </Etiqueta>
                      ))}
                    </div>
                  )}
                </article>
              )
            })}
          </div>
        </section>
      )}
    </Pagina>
  )
}

function Etiqueta({ tom, children }: { tom: 'bom' | 'risco'; children: string }) {
  const Icone = tom === 'bom' ? ThumbsUp : TriangleAlert
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        tom === 'bom'
          ? 'bg-green-50 text-green-700 dark:bg-green-950/60 dark:text-green-400'
          : 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400'
      }`}
    >
      <Icone size={12} aria-hidden />
      <span className="sr-only">{tom === 'bom' ? 'Ponto forte:' : 'Risco:'}</span>
      {children}
    </span>
  )
}

type GrupoPlano = { codigo: string; nome: string; nota: number; prioritaria: boolean; itens: ItemPlano[] }

/**
 * Plano de ação agrupado por dimensão (US06), com a dimensão prioritária e suas recomendações (US04).
 * Os grupos seguem a melhor posição de cada um, então a ordem da IA continua valendo entre eles.
 */
function agruparPorDimensao(avaliacao: Avaliacao): GrupoPlano[] {
  const grupos = new Map<string, GrupoPlano>()
  for (const item of avaliacao.recomendacoes) {
    const pontuacao = avaliacao.pontuacoes.find((p) => p.dimensao_codigo === item.dimensao_codigo)
    const grupo = grupos.get(item.dimensao_codigo) ?? {
      codigo: item.dimensao_codigo,
      nome: pontuacao?.dimensao_nome ?? item.dimensao_codigo,
      nota: item.nota_dimensao,
      prioritaria: pontuacao?.prioritaria ?? false,
      itens: [],
    }
    grupo.itens.push(item)
    grupos.set(item.dimensao_codigo, grupo)
  }
  return [...grupos.values()]
}

/** Baixa o relatório em PDF. O servidor tenta de novo se a geração falhar; se passar de 5 s, a pessoa tenta de novo. */
function useExportarPdf(avaliacaoId: string, aoExpirarSessao: () => void) {
  const [gerando, setGerando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function exportar() {
    setGerando(true)
    setErro(null)
    try {
      await baixarPdf(avaliacaoId)
    } catch (e) {
      if (e instanceof ErroApi && e.status === 401) return aoExpirarSessao()
      const detalhe = e instanceof ErroApi ? (e.detalhes as { detail?: string } | null)?.detail : undefined
      setErro(detalhe ?? 'Não foi possível gerar o PDF agora.')
    } finally {
      setGerando(false)
    }
  }

  return { gerando, erro, exportar }
}
