import { lazy, Suspense, useCallback, useState } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router'
import { sair } from '@/features/auth/authApi'
import { lerToken } from './api/cliente'
import { BarraLateral } from '@/components/BarraLateral'
import { Carregando } from '@/components/Pagina'
import { PaginaInicial } from '@/features/apresentacao/PaginaInicial'
import { Cadastro } from '@/features/auth/Cadastro'
import { Login } from '@/features/auth/Login'
import { RetornoGoogle } from '@/features/auth/RetornoGoogle'
import { PaginaEsqueciSenha, PaginaRedefinirSenha } from '@/features/auth/RecuperarSenha'
import { PaginaQuestionario } from '@/features/avaliacoes/PaginaQuestionario'
import { PaginaCatalogo } from '@/features/catalogo/PaginaCatalogo'
import { PaginaHistorico } from '@/features/historico/PaginaHistorico'

// Sob demanda: os gráficos (Recharts) só são baixados quando uma página com gráfico abre
const PaginaDashboard = lazy(() => import('@/features/dashboard/PaginaDashboard').then((m) => ({ default: m.PaginaDashboard })))
const PaginaResultado = lazy(() => import('@/features/avaliacoes/PaginaResultado').then((m) => ({ default: m.PaginaResultado })))
const PaginaUltimoResultado = lazy(() =>
  import('@/features/avaliacoes/PaginaResultado').then((m) => ({ default: m.PaginaUltimoResultado })),
)

// Primeira página da área logada (a apresentação pública fica em "/")
const PAGINA_INICIAL = '/dashboard'

/** Página que a pessoa tentou abrir antes de ir para o login. */
type EstadoLogin = { de?: string } | null

function App() {
  const [logado, setLogado] = useState(() => lerToken() !== null)

  const encerrarSessao = useCallback(() => {
    sair()
    setLogado(false)
  }, [])

  const entrou = useCallback(() => setLogado(true), [])

  return (
    <Routes>
      <Route path="/" element={<PaginaInicial logado={logado} destino={PAGINA_INICIAL} />} />
      <Route path="/login" element={<RotaLogin logado={logado} aoEntrar={entrou} />} />
      <Route path="/cadastro" element={logado ? <Navigate to={PAGINA_INICIAL} replace /> : <Cadastro aoEntrar={entrou} />} />
      <Route path="/entrar/google/retorno" element={<RetornoGoogle aoEntrar={entrou} destino={PAGINA_INICIAL} />} />
      <Route path="/recuperar-senha" element={<PaginaEsqueciSenha />} />
      <Route path="/redefinir-senha" element={<PaginaRedefinirSenha />} />
      <Route element={logado ? <LayoutLogado aoSair={encerrarSessao} /> : <IrParaLogin />}>
        <Route path="/dashboard" element={<PaginaDashboard aoExpirarSessao={encerrarSessao} />} />
        <Route path="/questionario" element={<PaginaQuestionario aoExpirarSessao={encerrarSessao} />} />
        <Route path="/resultados" element={<PaginaUltimoResultado aoExpirarSessao={encerrarSessao} />} />
        <Route path="/resultados/:id" element={<PaginaResultado aoExpirarSessao={encerrarSessao} />} />
        <Route path="/historico" element={<PaginaHistorico aoExpirarSessao={encerrarSessao} />} />
        <Route path="/catalogo" element={<PaginaCatalogo aoExpirarSessao={encerrarSessao} />} />
        <Route path="*" element={<Navigate to={PAGINA_INICIAL} replace />} />
      </Route>
    </Routes>
  )
}

function RotaLogin({ logado, aoEntrar }: { logado: boolean; aoEntrar: () => void }) {
  const { state } = useLocation()
  if (logado) {
    const de = (state as EstadoLogin)?.de
    return <Navigate to={de?.startsWith('/') ? de : PAGINA_INICIAL} replace />
  }
  return <Login aoEntrar={aoEntrar} />
}

/** Sem login (ou com a sessão expirada): vai para /login lembrando a página atual. */
function IrParaLogin() {
  const { pathname, search } = useLocation()
  return <Navigate to="/login" replace state={{ de: pathname + search } satisfies EstadoLogin} />
}

function LayoutLogado({ aoSair }: { aoSair: () => void }) {
  return (
    <div className="flex flex-1 flex-col lg:flex-row">
      <BarraLateral aoSair={aoSair} />
      <main className="flex min-w-0 flex-1 flex-col">
        <Suspense fallback={<Carregando />}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  )
}

export default App
