import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import {
  descartarRascunho,
  iniciarAvaliacao,
  obterQuestionario,
  type Avaliacao,
  type Questionario,
} from './avaliacoesApi'
import { ErroApi } from '@/api/cliente'
import { Botao } from '@/components/Botao'
import { Modal } from '@/components/Modal'
import { Carregando, MensagemPagina } from '@/components/Pagina'
import { Formulario } from './Formulario'

type Carga = { avaliacao: Avaliacao; questionario: Questionario }

/** Responder a avaliação atual (UC02): retoma o rascunho ou abre um novo. */
export function PaginaQuestionario({ aoExpirarSessao }: { aoExpirarSessao: () => void }) {
  const navigate = useNavigate()
  const [carga, setCarga] = useState<Carga | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  // Rascunho com respostas: pergunta se continua ou recomeça antes de mostrar o formulário (UC02 FA02)
  const [decidindo, setDecidindo] = useState(false)
  const [descartando, setDescartando] = useState(false)

  useEffect(() => {
    let ativo = true
    async function carregar() {
      const avaliacao = await iniciarAvaliacao()
      // Carrega a versão do rascunho, que pode não ser mais a ativa (US01)
      const questionario = await obterQuestionario(avaliacao.questionario)
      if (!ativo) return
      setCarga({ avaliacao, questionario })
      setDecidindo(avaliacao.respostas.length > 0)
    }
    carregar().catch((e) => {
      if (!ativo) return
      if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
      else if (e instanceof ErroApi && e.status === 404) setErro('Nenhum questionário foi publicado ainda.')
      else setErro('Não foi possível carregar a avaliação.')
    })
    return () => {
      ativo = false
    }
  }, [aoExpirarSessao])

  async function recomecar() {
    if (!carga) return
    setDescartando(true)
    try {
      await descartarRascunho(carga.avaliacao.id)
      setCarga({ ...carga, avaliacao: { ...carga.avaliacao, respostas: [] } })
      setDecidindo(false)
    } catch (e) {
      if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
      else setErro('Não foi possível apagar as respostas. Tente de novo.')
    } finally {
      setDescartando(false)
    }
  }

  if (erro) return <MensagemPagina tipo="erro">{erro}</MensagemPagina>
  if (!carga) return <Carregando texto="Carregando o questionário…" />
  if (decidindo) {
    const total = carga.avaliacao.respostas.length
    return (
      <Modal
        aberto
        titulo="Continuar de onde parou?"
        aoFechar={() => setDecidindo(false)}
        acoes={
          <>
            <Botao variante="secundario" onClick={recomecar} disabled={descartando}>
              {descartando ? 'Apagando…' : 'Recomeçar do zero'}
            </Botao>
            {/* Foco no caminho seguro: Enter não apaga respostas sem querer */}
            <Botao onClick={() => setDecidindo(false)} disabled={descartando} autoFocus>
              Continuar
            </Botao>
          </>
        }
      >
        <p>
          Você já respondeu {total} {total === 1 ? 'pergunta' : 'perguntas'} deste questionário. Continue de onde parou
          ou recomece: ao recomeçar, as respostas salvas são apagadas.
        </p>
      </Modal>
    )
  }
  return (
    <Formulario
      // A key recria o formulário depois de recomeçar, sem as respostas antigas em memória
      key={carga.avaliacao.respostas.length === 0 ? 'vazio' : 'retomado'}
      avaliacao={carga.avaliacao}
      questionario={carga.questionario}
      // Ao enviar, vai para o resultado com a mensagem de conclusão (UC02, passo 9)
      aoSubmeter={(avaliacao) => navigate(`/resultados/${avaliacao.id}`, { state: { enviada: true } })}
      aoSalvarESair={() => navigate('/dashboard')}
    />
  )
}
