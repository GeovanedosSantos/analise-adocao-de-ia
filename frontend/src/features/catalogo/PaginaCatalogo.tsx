import { useEffect, useState, type ReactNode } from 'react'
import { ErroApi } from '@/api/cliente'
import { Alerta } from '@/components/Alerta'
import { Cartao, Carregando, MensagemPagina, Pagina } from '@/components/Pagina'
import { CartaoRecomendacao } from './CartaoRecomendacao'
import { listarCatalogo, type Recomendacao } from './catalogoApi'

type Props = { aoExpirarSessao: () => void }

type Grupo = { codigo: string; nome: string; itens: Recomendacao[] }

/** Catálogo de recomendações (UC06): todas as ações ativas, agrupadas por dimensão e ordenadas pela faixa de nota. */
export function PaginaCatalogo({ aoExpirarSessao }: Props) {
  const [catalogo, setCatalogo] = useState<Recomendacao[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [filtro, setFiltro] = useState<string | null>(null)

  useEffect(() => {
    let ativo = true
    listarCatalogo()
      .then((dados) => ativo && setCatalogo(dados))
      .catch((e) => {
        if (!ativo) return
        if (e instanceof ErroApi && e.status === 401) aoExpirarSessao()
        else setErro('Não foi possível carregar o catálogo.')
      })
    return () => {
      ativo = false
    }
  }, [aoExpirarSessao])

  if (erro) return <MensagemPagina tipo="erro">{erro}</MensagemPagina>
  if (!catalogo) return <Carregando />

  const grupos = agrupar(catalogo)
  const visiveis = grupos.filter((g) => filtro === null || g.codigo === filtro)

  return (
    <Pagina
      titulo="Catálogo de recomendações"
      descricao="Ações curadas por especialistas. Cada avaliação recebe as que se aplicam à nota de cada dimensão."
    >
      {grupos.length === 0 ? (
        <Alerta titulo="Catálogo vazio">Nenhuma recomendação foi cadastrada ainda.</Alerta>
      ) : (
        <>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por dimensão">
            <Filtro ativo={filtro === null} aoClicar={() => setFiltro(null)}>
              Todas ({catalogo.length})
            </Filtro>
            {grupos.map((g) => (
              <Filtro key={g.codigo} ativo={filtro === g.codigo} aoClicar={() => setFiltro(g.codigo)}>
                {g.nome} ({g.itens.length})
              </Filtro>
            ))}
          </div>
          {visiveis.map((g) => (
            <Cartao key={g.codigo} titulo={g.nome}>
              <div className="grid items-start gap-3 lg:grid-cols-2">
                {g.itens.map((r) => (
                  <CartaoRecomendacao key={r.id} recomendacao={r} contexto={`Nota de ${faixa(r)}`} />
                ))}
              </div>
            </Cartao>
          ))}
        </>
      )}
    </Pagina>
  )
}

/** Mantém a ordem da API (dimensão, depois faixa de nota). */
function agrupar(catalogo: Recomendacao[]): Grupo[] {
  const grupos = new Map<string, Grupo>()
  for (const r of catalogo) {
    const grupo = grupos.get(r.dimensao_codigo) ?? { codigo: r.dimensao_codigo, nome: r.dimensao_nome, itens: [] }
    grupo.itens.push(r)
    grupos.set(r.dimensao_codigo, grupo)
  }
  return [...grupos.values()]
}

function faixa({ nota_minima, nota_maxima }: Recomendacao) {
  // A máxima é exclusiva, exceto 100
  return nota_maxima === 100 ? `${nota_minima} a 100` : `${nota_minima} até menos de ${nota_maxima}`
}

function Filtro({ ativo, aoClicar, children }: { ativo: boolean; aoClicar: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={ativo}
      onClick={aoClicar}
      className={`h-8 touch-manipulation rounded-full border px-3 text-sm font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-destaque ${
        ativo ? 'border-destaque bg-destaque text-sobre-destaque' : 'border-borda bg-superficie text-titulo hover:bg-suave'
      }`}
    >
      {children}
    </button>
  )
}
