import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { iniciarAvaliacao, obterQuestionario, type Avaliacao, type Questionario } from './avaliacoesApi'
import { ErroApi } from '@/api/cliente'
import { Carregando, MensagemPagina } from '@/components/Pagina'
import { Formulario } from './Formulario'

type Carga = { avaliacao: Avaliacao; questionario: Questionario }

/** Responder a avaliação atual (UC02): retoma o rascunho ou abre um novo. */
export function PaginaQuestionario({ aoExpirarSessao }: { aoExpirarSessao: () => void }) {
  const navigate = useNavigate()
  const [carga, setCarga] = useState<Carga | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    async function carregar() {
      const avaliacao = await iniciarAvaliacao()
      // Carrega a versão do rascunho, que pode não ser mais a ativa (US01)
      const questionario = await obterQuestionario(avaliacao.questionario)
      if (ativo) setCarga({ avaliacao, questionario })
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

  if (erro) return <MensagemPagina tipo="erro">{erro}</MensagemPagina>
  if (!carga) return <Carregando texto="Carregando o questionário…" />
  return (
    <Formulario
      avaliacao={carga.avaliacao}
      questionario={carga.questionario}
      // Ao enviar, vai para o resultado com a mensagem de conclusão (UC02, passo 9)
      aoSubmeter={(avaliacao) => navigate(`/resultados/${avaliacao.id}`, { state: { enviada: true } })}
    />
  )
}
