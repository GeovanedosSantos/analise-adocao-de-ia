import { useEffect, useState } from 'react'
import { iniciarAvaliacao, obterQuestionario, type Avaliacao, type Questionario } from './avaliacoesApi'
import { ErroApi } from '@/api/cliente'
import { Formulario } from './Formulario'
import { Resultado } from './Resultado'

type Carga = { avaliacao: Avaliacao; questionario: Questionario }

export function PaginaAvaliacao({ aoExpirarSessao }: { aoExpirarSessao: () => void }) {
  const [carga, setCarga] = useState<Carga | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    async function carregar() {
      const avaliacao = await iniciarAvaliacao()
      // Carrega a versão do rascunho, que pode não ser mais a ativa (US03)
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

  if (erro) return <p role="alert" className="p-6 text-red-600">{erro}</p>
  if (!carga) return <p className="p-6">Carregando…</p>
  if (carga.avaliacao.status !== 'DRAFT') return <Resultado avaliacao={carga.avaliacao} />
  return (
    <Formulario
      avaliacao={carga.avaliacao}
      questionario={carga.questionario}
      aoSubmeter={(avaliacao) => setCarga({ ...carga, avaliacao })}
    />
  )
}
