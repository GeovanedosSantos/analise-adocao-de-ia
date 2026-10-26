import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

type Tema = 'light' | 'dark'

const CHAVE = 'tema'
const sistema = () => window.matchMedia('(prefers-color-scheme: dark)')

function escolhaSalva(): 'claro' | 'escuro' | null {
  try {
    const valor = localStorage.getItem(CHAVE)
    return valor === 'claro' || valor === 'escuro' ? valor : null
  } catch {
    return null
  }
}

function aplicar(tema: Tema) {
  document.documentElement.dataset.theme = tema
}

/**
 * Botão sol/lua. Sem escolha salva, o tema acompanha o sistema (inclusive se ele mudar com a página aberta);
 * ao clicar, a escolha fica salva e passa a valer sobre o sistema. O tema inicial é aplicado no index.html.
 */
export function AlternarTema({ className = '' }: { className?: string }) {
  const [tema, setTema] = useState<Tema>(() => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'))

  useEffect(() => {
    const consulta = sistema()
    function mudouNoSistema(evento: MediaQueryListEvent) {
      if (escolhaSalva()) return
      const novo = evento.matches ? 'dark' : 'light'
      aplicar(novo)
      setTema(novo)
    }
    consulta.addEventListener('change', mudouNoSistema)
    return () => consulta.removeEventListener('change', mudouNoSistema)
  }, [])

  function alternar() {
    const novo = tema === 'dark' ? 'light' : 'dark'
    aplicar(novo)
    setTema(novo)
    try {
      localStorage.setItem(CHAVE, novo === 'dark' ? 'escuro' : 'claro')
    } catch {
      // Sem storage: a escolha vale só até recarregar
    }
  }

  const escuro = tema === 'dark'
  const Icone = escuro ? Sun : Moon
  return (
    <button
      type="button"
      onClick={alternar}
      aria-label={escuro ? 'Usar tema claro' : 'Usar tema escuro'}
      title={escuro ? 'Usar tema claro' : 'Usar tema escuro'}
      className={`grid size-9 touch-manipulation place-items-center rounded-lg text-texto transition-[transform,background-color] duration-150 ease-saida hover:bg-suave hover:text-titulo focus-visible:outline-2 focus-visible:outline-destaque active:scale-[0.94] ${className}`}
    >
      {/* key: o ícone novo entra girando de leve (só transform/opacity) */}
      <Icone
        key={tema}
        size={18}
        aria-hidden
        className="transition-[rotate,opacity] duration-200 ease-saida starting:-rotate-45 starting:opacity-0"
      />
    </button>
  )
}
