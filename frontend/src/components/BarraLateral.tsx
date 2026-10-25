import { useRef, useState } from 'react'
import {
  BookOpen,
  ChartColumn,
  ClipboardList,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  type LucideIcon,
} from 'lucide-react'
import { Link, NavLink } from 'react-router'
import { AlternarTema } from './AlternarTema'
import { Logo } from './Logo'

type ItemNavegacao = { para: string; rotulo: string; icone: LucideIcon }

// Uma entrada por caso de uso do usuário (UC02 a UC06). "Resultados" fica ativo também em /resultados/:id
const SECOES: { titulo: string; itens: ItemNavegacao[] }[] = [
  {
    titulo: 'Avaliação',
    itens: [
      { para: '/dashboard', rotulo: 'Dashboard', icone: LayoutDashboard },
      { para: '/questionario', rotulo: 'Questionário', icone: ClipboardList },
      { para: '/resultados', rotulo: 'Resultados', icone: ChartColumn },
      { para: '/historico', rotulo: 'Histórico', icone: History },
    ],
  },
  { titulo: 'Conteúdo', itens: [{ para: '/catalogo', rotulo: 'Catálogo', icone: BookOpen }] },
]

const CHAVE_RECOLHIDA = 'barra_lateral_recolhida'

function lerRecolhida() {
  try {
    return localStorage.getItem(CHAVE_RECOLHIDA) === '1'
  } catch {
    return false
  }
}

/** Navegação das páginas logadas: barra lateral no desktop, gaveta no celular. */
export function BarraLateral({ aoSair }: { aoSair: () => void }) {
  const [recolhida, setRecolhida] = useState(lerRecolhida)
  const gaveta = useRef<HTMLDialogElement>(null)

  function alternar() {
    const nova = !recolhida
    setRecolhida(nova)
    try {
      localStorage.setItem(CHAVE_RECOLHIDA, nova ? '1' : '0')
    } catch {
      // Sem storage: a preferência vale só até recarregar
    }
  }

  return (
    <>
      {/* Desktop: coluna fixa à esquerda, que recolhe para só os ícones */}
      <aside
        className={`sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-borda bg-superficie lg:flex ${recolhida ? 'w-17' : 'w-64'}`}
      >
        <div className={`flex h-16 items-center gap-2 px-3 ${recolhida ? 'justify-center' : 'justify-between'}`}>
          {!recolhida && <Marca />}
          <button
            type="button"
            onClick={alternar}
            aria-label={recolhida ? 'Expandir menu' : 'Recolher menu'}
            title={recolhida ? 'Expandir menu' : 'Recolher menu'}
            className="rounded-md p-2 text-texto hover:bg-suave hover:text-titulo focus-visible:outline-2 focus-visible:outline-destaque"
          >
            {recolhida ? <PanelLeftOpen size={18} aria-hidden /> : <PanelLeftClose size={18} aria-hidden />}
          </button>
        </div>
        <Navegacao recolhida={recolhida} aoSair={aoSair} />
      </aside>

      {/* Celular e tablet: barra no topo com botão que abre a gaveta */}
      <div className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-borda bg-superficie px-4 lg:hidden">
        <Marca />
        <button
          type="button"
          onClick={() => gaveta.current?.showModal()}
          aria-label="Abrir menu"
          className="touch-manipulation rounded-md p-2 text-titulo hover:bg-suave focus-visible:outline-2 focus-visible:outline-destaque"
        >
          <Menu size={20} aria-hidden />
        </button>
      </div>
      <dialog
        ref={gaveta}
        aria-label="Menu"
        // Clique no fundo escuro (fora do conteúdo) fecha a gaveta
        onClick={(e) => e.target === e.currentTarget && gaveta.current?.close()}
        className="fixed inset-y-0 left-0 m-0 h-dvh max-h-none w-72 max-w-[85vw] bg-superficie p-0 text-texto shadow-xl transition-[translate,display,overlay] transition-discrete duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] backdrop:bg-black/40 not-open:-translate-x-full starting:open:-translate-x-full lg:hidden"
      >
        <div className="flex h-full flex-col">
          <div className="flex h-14 items-center justify-between px-4">
            <Marca />
            <button
              type="button"
              onClick={() => gaveta.current?.close()}
              aria-label="Fechar menu"
              // Ao abrir, o foco vai para o fechar, não para o primeiro link
              autoFocus
              className="touch-manipulation rounded-md p-2 text-titulo hover:bg-suave focus-visible:outline-2 focus-visible:outline-destaque"
            >
              <X size={20} aria-hidden />
            </button>
          </div>
          <Navegacao recolhida={false} aoSair={aoSair} aoNavegar={() => gaveta.current?.close()} />
        </div>
      </dialog>
    </>
  )
}

function Marca() {
  return (
    <Link to="/" aria-label="Adoção de IA, ir para o início" className="min-w-0 rounded-md focus-visible:outline-2 focus-visible:outline-destaque">
      <Logo />
    </Link>
  )
}

type PropsNavegacao = { recolhida: boolean; aoSair: () => void; aoNavegar?: () => void }

function Navegacao({ recolhida, aoSair, aoNavegar }: PropsNavegacao) {
  const item = `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-destaque ${recolhida ? 'justify-center' : ''}`
  return (
    <>
      <nav aria-label="Principal" className="flex flex-1 flex-col gap-6 overflow-y-auto overscroll-contain px-3 py-2">
        {SECOES.map((secao) => (
          <div key={secao.titulo} className="flex flex-col gap-1">
            {recolhida ? (
              <hr className="mx-2 mb-1 border-borda" />
            ) : (
              <p className="px-3 pb-1 text-xs font-medium tracking-wide uppercase">{secao.titulo}</p>
            )}
            <ul className="flex flex-col gap-0.5">
              {secao.itens.map(({ para, rotulo, icone: Icone }) => (
                <li key={para}>
                  <NavLink
                    to={para}
                    onClick={aoNavegar}
                    aria-label={recolhida ? rotulo : undefined}
                    title={recolhida ? rotulo : undefined}
                    className={({ isActive }) =>
                      `${item} ${isActive ? 'bg-destaque-fundo text-destaque' : 'text-texto hover:bg-suave hover:text-titulo'}`
                    }
                  >
                    <Icone size={18} aria-hidden className="shrink-0" />
                    {!recolhida && rotulo}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <div className={`flex gap-1 border-t border-borda p-3 ${recolhida ? 'flex-col items-center' : 'items-center'}`}>
        <button
          type="button"
          onClick={aoSair}
          aria-label={recolhida ? 'Sair' : undefined}
          title={recolhida ? 'Sair' : undefined}
          className={`${item} w-full text-texto hover:bg-suave hover:text-titulo`}
        >
          <LogOut size={18} aria-hidden className="shrink-0" />
          {!recolhida && 'Sair'}
        </button>
        <AlternarTema className="shrink-0" />
      </div>
    </>
  )
}
