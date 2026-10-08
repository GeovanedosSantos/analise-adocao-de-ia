import { useState } from 'react'
import { submeterAvaliacao, type Avaliacao, type Pergunta, type Questionario } from './avaliacoesApi'
import { ErroApi } from '@/api/cliente'
import type { ItemRascunho } from './rascunho/agendador'
import { useRascunho } from './rascunho/useRascunho'

// Escala de concordância em linguagem acessível a gestores (RNF07)
const ESCALA = ['Discordo totalmente', 'Discordo', 'Neutro', 'Concordo', 'Concordo totalmente']

const TEXTO_ESTADO = { salvando: 'Salvando rascunho…', salvo: 'Rascunho salvo', erro: 'Sem conexão: tentaremos salvar de novo' }

type Valores = Record<string, { valor_objetivo?: number | null; texto_aberto?: string }>

type Props = { avaliacao: Avaliacao; questionario: Questionario; aoSubmeter: (avaliacao: Avaliacao) => void }

export function Formulario({ avaliacao, questionario, aoSubmeter }: Props) {
  const { agendador, estado } = useRascunho(avaliacao.id)
  const [valores, setValores] = useState<Valores>(() =>
    Object.fromEntries(avaliacao.respostas.map((r) => [r.pergunta, r])),
  )
  const [enviando, setEnviando] = useState(false)
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
      setErro(
        e instanceof ErroApi && e.status === 400
          ? 'Responda todas as perguntas objetivas antes de enviar.'
          : 'Não foi possível enviar agora. Suas respostas estão salvas; tente de novo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="flex flex-col gap-8 p-6">
      <div className="flex items-baseline justify-between gap-4">
        <p className="text-sm">Questionário v{questionario.versao}</p>
        <p className="text-sm" aria-live="polite">{estado && TEXTO_ESTADO[estado]}</p>
      </div>

      {questionario.dimensoes.map((dimensao) => (
        <section key={dimensao.id} className="flex flex-col gap-6">
          <h2>{dimensao.nome}</h2>
          {dimensao.perguntas.map((pergunta) => (
            <CampoPergunta
              key={pergunta.id}
              pergunta={pergunta}
              valor={valores[pergunta.id]}
              aoResponder={responder}
            />
          ))}
        </section>
      ))}

      {erro && <p role="alert" className="text-red-600">{erro}</p>}
      <button
        type="button"
        onClick={submeter}
        disabled={enviando || faltam > 0}
        className="self-start rounded bg-destaque px-5 py-2 font-medium text-white disabled:opacity-60"
      >
        {enviando ? 'Enviando…' : faltam > 0 ? `Faltam ${faltam} perguntas objetivas` : 'Enviar avaliação'}
      </button>
    </div>
  )
}

type PropsCampo = { pergunta: Pergunta; valor: Valores[string] | undefined; aoResponder: (item: ItemRascunho) => void }

function CampoPergunta({ pergunta, valor, aoResponder }: PropsCampo) {
  if (pergunta.tipo === 'DISSERTATIVA') {
    return (
      <label className="flex flex-col gap-2">
        <span className="text-titulo">{pergunta.texto}</span>
        <textarea
          className="min-h-28 rounded border border-borda bg-fundo p-3 text-titulo"
          maxLength={5000}
          value={valor?.texto_aberto ?? ''}
          onChange={(e) => aoResponder({ pergunta: pergunta.id, texto_aberto: e.target.value })}
        />
      </label>
    )
  }
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-titulo">{pergunta.texto}</legend>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
        {ESCALA.map((rotulo, i) => (
          <label
            key={rotulo}
            className="flex cursor-pointer items-center gap-2 rounded border border-borda px-3 py-2 text-sm has-checked:border-destaque has-checked:bg-destaque-fundo"
          >
            <input
              type="radio"
              name={pergunta.id}
              checked={valor?.valor_objetivo === i + 1}
              onChange={() => aoResponder({ pergunta: pergunta.id, valor_objetivo: i + 1 })}
            />
            {rotulo}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
