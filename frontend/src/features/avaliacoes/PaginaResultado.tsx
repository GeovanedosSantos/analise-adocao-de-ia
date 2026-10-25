import { useEffect, useState } from 'react'
import { Navigate, useLocation, useParams } from 'react-router'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { BotaoLink } from '@/components/Botao'
import { listarAvaliacoes, obterAvaliacao, type Avaliacao } from './avaliacoesApi'
import { Resultado } from './Resultado'

type Props = { aoExpirarSessao: () => void }

/** /resultados: abre o resultado da avaliação enviada mais recente (UC03). */
export function PaginaUltimoResultado({ aoExpirarSessao }: Props) {
  const [ultimaId, setUltimaId] = useState<string | null | undefined>(undefined)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    listarAvaliacoes()
      .then((avaliacoes) => {
        // A listagem vem da mais recente para a mais antiga; o rascunho não tem resultado
        if (ativo) setUltimaId(avaliacoes.find((a) => a.status !== 'DRAFT')?.id ?? null)
      })
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        else setErro('Não foi possível carregar os resultados.')
      })
    return () => {
      ativo = false
    }
  }, [aoExpirarSessao])

  if (erro) return <Mensagem tipo="erro">{erro}</Mensagem>
  if (ultimaId === undefined) return <p className="p-6">Carregando…</p>
  if (ultimaId === null) {
    return (
      <Mensagem titulo="Nenhum resultado ainda" acao={<BotaoLink to="/questionario">Responder questionário</BotaoLink>}>
        Responda o questionário para ver a pontuação da sua empresa.
      </Mensagem>
    )
  }
  return <Navigate to={`/resultados/${ultimaId}`} replace />
}

/** /resultados/:id: o resultado de uma avaliação específica, vinda do envio ou do histórico. */
export function PaginaResultado({ aoExpirarSessao }: Props) {
  const { id = '' } = useParams()
  // A key recria a página ao trocar de avaliação, sem reaproveitar o estado da anterior
  return <ResultadoDaAvaliacao key={id} id={id} aoExpirarSessao={aoExpirarSessao} />
}

function ResultadoDaAvaliacao({ id, aoExpirarSessao }: Props & { id: string }) {
  const { state } = useLocation()
  const [avaliacao, setAvaliacao] = useState<Avaliacao | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    obterAvaliacao(id)
      .then((dados) => ativo && setAvaliacao(dados))
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        // 403: avaliação de outra empresa; 404: não existe. Para o usuário, as duas são "não encontrada"
        else if (e instanceof ErroApi && (e.status === 403 || e.status === 404)) setErro('Avaliação não encontrada.')
        else setErro('Não foi possível carregar o resultado.')
      })
    return () => {
      ativo = false
    }
  }, [id, aoExpirarSessao])

  if (erro) return <Mensagem tipo="erro">{erro}</Mensagem>
  if (!avaliacao) return <p className="p-6">Carregando…</p>
  if (avaliacao.status === 'DRAFT') {
    return (
      <Mensagem titulo="Avaliação ainda não enviada" acao={<BotaoLink to="/questionario">Continuar respondendo</BotaoLink>}>
        O resultado aparece depois que o questionário é enviado.
      </Mensagem>
    )
  }
  const enviada = (state as { enviada?: boolean } | null)?.enviada === true
  return <Resultado avaliacao={avaliacao} enviada={enviada} aoExpirarSessao={aoExpirarSessao} />
}

function Mensagem(props: Parameters<typeof Alerta>[0]) {
  return (
    <div className="p-6">
      <Alerta {...props} />
    </div>
  )
}
