import { useEffect, useState } from 'react'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao, BotaoLink } from '@/components/Botao'
import { ResumoAvaliacao } from '@/components/ResumoAvaliacao'
import { Sparkles, ThumbsUp, TriangleAlert } from 'lucide-react'
import { Cartao, Pagina } from '@/components/Pagina'
import { acompanharProcessamento } from './acompanhamento'
import { ExploradorDimensoes } from './ExploradorDimensoes'
import { consultarStatus, obterAvaliacao, type Avaliacao } from './avaliacoesApi'

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

  return (
    <Pagina
      titulo="Resultado da avaliação"
      descricao={`Enviada em ${data} · questionário v${avaliacao.versao_questionario}`}
      acoes={
        <BotaoLink to="/historico" variante="secundario">
          Ver histórico
        </BotaoLink>
      }
    >
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
