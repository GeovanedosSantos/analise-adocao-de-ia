import { useState } from 'react'
import { submeterAvaliacao, type Avaliacao, type Pergunta, type Questionario } from './avaliacoesApi'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Botao } from '@/components/Botao'
import { Modal } from '@/components/Modal'
import { Cartao, Pagina } from '@/components/Pagina'
import type { ItemRascunho } from './rascunho/agendador'
import { useRascunho } from './rascunho/useRascunho'

// Escala de concordância em linguagem acessível a gestores (RNF07)
const ESCALA = ['Discordo totalmente', 'Discordo', 'Neutro', 'Concordo', 'Concordo totalmente']

const TEXTO_ESTADO = { salvando: 'Salvando rascunho…', salvo: 'Rascunho salvo', erro: 'Sem conexão: tentaremos salvar de novo' }

type Valores = Record<string, { valor_objetivo?: number | null; texto_aberto?: string }>

type Props = {
  avaliacao: Avaliacao
  questionario: Questionario
  aoSubmeter: (avaliacao: Avaliacao) => void
  /** "Salvar e continuar depois" (UC02 FA01): chamado depois que o rascunho termina de salvar. */
  aoSalvarESair: () => void
}

export function Formulario({ avaliacao, questionario, aoSubmeter, aoSalvarESair }: Props) {
  const { agendador, estado } = useRascunho(avaliacao.id)
  const [valores, setValores] = useState<Valores>(() =>
    Object.fromEntries(avaliacao.respostas.map((r) => [r.pergunta, r])),
  )
  const [confirmando, setConfirmando] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [saindo, setSaindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const objetivas = questionario.dimensoes.flatMap((d) => d.perguntas).filter((p) => p.tipo === 'OBJETIVA')
  const faltam = objetivas.filter((p) => !valores[p.id]?.valor_objetivo).length

  function responder(item: ItemRascunho) {
    setValores((anteriores) => ({ ...anteriores, [item.pergunta]: { ...anteriores[item.pergunta], ...item } }))
    agendador.registrar(item)
  }

  async function submeter() {
    setEnviando(true)
    setErro(null)
    try {
      await agendador.descarregar()
      aoSubmeter(await submeterAvaliacao(avaliacao.id))
    } catch (e) {
      setConfirmando(false)
      setErro(
        e instanceof ErroApi && e.status === 400
          ? 'Responda todas as perguntas objetivas antes de enviar.'
          : 'Não foi possível enviar agora. Suas respostas estão salvas; tente de novo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  async function salvarESair() {
    setSaindo(true)
    setErro(null)
    try {
      await agendador.descarregar()
      aoSalvarESair()
    } catch {
      setErro('Não foi possível salvar agora. Verifique a conexão e tente de novo.')
      setSaindo(false)
    }
  }

  const respondidas = objetivas.length - faltam
  const progresso = objetivas.length ? (respondidas / objetivas.length) * 100 : 0

  return (
    <>
      <Pagina
        titulo="Questionário"
        descricao={
          <>
            Versão {questionario.versao} · as respostas são salvas automaticamente
            <span aria-live="polite" className="ml-2 font-medium text-titulo">
              {estado && TEXTO_ESTADO[estado]}
            </span>
          </>
        }
      >
        {questionario.dimensoes.map((dimensao, i) => (
          <Cartao key={dimensao.id} titulo={`${i + 1}. ${dimensao.nome}`} descricao={dimensao.descricao || undefined}>
            <div className="flex flex-col gap-8">
              {dimensao.perguntas.map((pergunta) => (
                <CampoPergunta
                  key={pergunta.id}
                  pergunta={pergunta}
                  valor={valores[pergunta.id]}
                  aoResponder={responder}
                />
              ))}
            </div>
          </Cartao>
        ))}
        {erro && <Alerta tipo="erro">{erro}</Alerta>}
      </Pagina>

      {/* Rodapé fixo: progresso e envio sempre à mão, sem rolar até o fim */}
      <div className="sticky bottom-0 border-t border-borda bg-superficie/95 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex min-w-48 flex-1 flex-col gap-1.5">
            <p className="text-sm">
              <span className="font-semibold text-titulo tabular-nums">
                {respondidas} de {objetivas.length}
              </span>{' '}
              perguntas objetivas respondidas
            </p>
            <div
              className="h-1.5 overflow-hidden rounded-full bg-suave"
              role="progressbar"
              aria-label="Perguntas objetivas respondidas"
              aria-valuenow={respondidas}
              aria-valuemin={0}
              aria-valuemax={objetivas.length}
            >
              {/* transform em vez de width: anima só na GPU */}
              <div
                className="h-full origin-left rounded-full bg-destaque transition-transform duration-200 ease-saida"
                style={{ transform: `scaleX(${progresso / 100})` }}
              />
            </div>
          </div>
          <Botao variante="secundario" onClick={salvarESair} disabled={saindo || enviando}>
            {saindo ? 'Salvando…' : 'Salvar e continuar depois'}
          </Botao>
          <Botao onClick={() => setConfirmando(true)} disabled={faltam > 0 || saindo}>
            {faltam > 0 ? `Faltam ${faltam}` : 'Enviar avaliação'}
          </Botao>
        </div>
      </div>

      <Modal
        aberto={confirmando}
        titulo="Enviar a avaliação?"
        aoFechar={() => !enviando && setConfirmando(false)}
        acoes={
          <>
            <Botao variante="secundario" onClick={() => setConfirmando(false)} disabled={enviando}>
              Voltar e revisar
            </Botao>
            <Botao onClick={submeter} disabled={enviando}>
              {enviando ? 'Enviando…' : 'Enviar avaliação'}
            </Botao>
          </>
        }
      >
        <p>
          Depois do envio, as respostas não podem mais ser alteradas. As notas saem na hora; a análise das respostas
          abertas pode levar alguns minutos.
        </p>
      </Modal>
    </>
  )
}

type PropsCampo = { pergunta: Pergunta; valor: Valores[string] | undefined; aoResponder: (item: ItemRascunho) => void }

function CampoPergunta({ pergunta, valor, aoResponder }: PropsCampo) {
  if (pergunta.tipo === 'DISSERTATIVA') {
    return (
      <label className="flex flex-col gap-3">
        <span className="flex flex-col gap-1">
          <span className="text-xs font-medium tracking-wide uppercase">Resposta aberta · opcional</span>
          <span className="font-medium text-titulo">{pergunta.texto}</span>
        </span>
        <textarea
          className="min-h-28 rounded-lg border border-borda bg-superficie p-3 text-base text-titulo shadow-xs outline-none focus:border-destaque focus:ring-3 focus:ring-destaque/20 sm:text-sm"
          maxLength={5000}
          value={valor?.texto_aberto ?? ''}
          onChange={(e) => aoResponder({ pergunta: pergunta.id, texto_aberto: e.target.value })}
        />
      </label>
    )
  }
  return (
    <fieldset className="flex flex-col">
      <legend className="mb-3 flex flex-col gap-1">
        {pergunta.fator && <span className="text-xs font-medium tracking-wide uppercase">{pergunta.fator}</span>}
        <span className="font-medium text-titulo">{pergunta.texto}</span>
      </legend>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
        {ESCALA.map((rotulo, i) => (
          // O radio fica visível (foco e leitor de tela nativos); o cartão inteiro é a área de clique
          <label
            key={rotulo}
            className="selecionavel flex cursor-pointer touch-manipulation items-center gap-2.5 rounded-lg border border-borda px-3 py-2.5 text-sm text-titulo transition-[background-color,border-color,translate] duration-150 ease-saida hover:-translate-y-0.5 hover:bg-suave has-checked:border-destaque has-checked:bg-destaque-fundo has-checked:font-medium has-focus-visible:outline-2 has-focus-visible:outline-destaque"
          >
            <input
              type="radio"
              name={pergunta.id}
              checked={valor?.valor_objetivo === i + 1}
              onChange={() => aoResponder({ pergunta: pergunta.id, valor_objetivo: i + 1 })}
              className="size-4 shrink-0"
            />
            {rotulo}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
