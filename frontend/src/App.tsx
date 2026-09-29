import { useCallback, useState } from 'react'
import { sair } from '@/features/auth/authApi'
import { lerToken } from './api/cliente'
import { Login } from '@/features/auth/Login'
import { PaginaAvaliacao } from '@/features/avaliacoes/PaginaAvaliacao'

function App() {
  const [logado, setLogado] = useState(() => lerToken() !== null)

  const encerrarSessao = useCallback(() => {
    sair()
    setLogado(false)
  }, [])

  return (
    <main className="flex flex-col">
      <header className="flex items-center justify-between gap-4 border-b border-borda px-6">
        <div>
          <h1>Análise de adoção de IA</h1>
          <p className="mb-6">Avaliação de prontidão organizacional para adoção de IA em empresas.</p>
        </div>
        {logado && (
          <button type="button" onClick={encerrarSessao} className="text-sm underline">
            Sair
          </button>
        )}
      </header>
      {logado ? <PaginaAvaliacao aoExpirarSessao={encerrarSessao} /> : <Login aoEntrar={() => setLogado(true)} />}
    </main>
  )
}

export default App
