import { BookOpen, ChartColumn, ClipboardList, History, LayoutDashboard, LogOut, type LucideIcon } from 'lucide-react'
import { Link, NavLink } from 'react-router'
import { Botao } from './Botao'

type ItemNavegacao = { para: string; rotulo: string; icone: LucideIcon }

// Uma entrada por caso de uso do usuário (UC02 a UC06). "Resultados" fica ativo também em /resultados/:id
const NAVEGACAO: ItemNavegacao[] = [
  { para: '/dashboard', rotulo: 'Dashboard', icone: LayoutDashboard },
  { para: '/questionario', rotulo: 'Questionário', icone: ClipboardList },
  { para: '/resultados', rotulo: 'Resultados', icone: ChartColumn },
  { para: '/historico', rotulo: 'Histórico', icone: History },
  { para: '/catalogo', rotulo: 'Catálogo', icone: BookOpen },
]

/** Cabeçalho das páginas de quem está logado: nome do sistema, navegação e saída. */
export function Cabecalho({ aoSair }: { aoSair: () => void }) {
  return (
    <header className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-borda bg-superficie px-6 py-4">
      <Link to="/" className="text-lg font-medium text-titulo">
        Análise de adoção de IA
      </Link>

      <nav aria-label="Principal" className="order-last w-full md:order-0 md:w-auto">
        <ul className="flex flex-wrap gap-1">
          {NAVEGACAO.map(({ para, rotulo, icone: Icone }) => (
            <li key={para}>
              <NavLink
                to={para}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-destaque ${
                    isActive ? 'bg-destaque-fundo text-destaque' : 'text-texto hover:text-titulo'
                  }`
                }
              >
                <Icone size={18} aria-hidden="true" />
                {rotulo}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* ml-auto empurra o Sair para a direita; título e links ficam juntos à esquerda */}
      <Botao variante="secundario" onClick={aoSair} className="ml-auto text-sm">
        <LogOut size={16} aria-hidden="true" />
        Sair
      </Botao>
    </header>
  )
}
