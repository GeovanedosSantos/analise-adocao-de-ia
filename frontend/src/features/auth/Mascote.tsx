import { useEffect, useRef } from 'react'

export type EstadoMascote = 'ocioso' | 'usuario' | 'senha' | 'espiando' | 'pensando' | 'triste'

const FALAS: Record<EstadoMascote, string> = {
  ocioso: 'Oi! Eu sou a Ada, a IA que analisa a prontidão da sua empresa.',
  usuario: 'Prazer! Qual é o seu usuário?',
  senha: 'Pode digitar, não estou olhando.',
  espiando: 'Opa… prometo esquecer o que vi.',
  pensando: 'Conferindo seu acesso…',
  triste: 'Hmm, não reconheci esse acesso. Vamos tentar de novo?',
}

// Para onde os olhos vão em cada estado (em unidades do SVG); no ocioso, seguem o cursor
const OLHAR: Partial<Record<EstadoMascote, [number, number]>> = {
  usuario: [-2, 4],
  pensando: [3, -4],
  triste: [0, 3],
}
const ALCANCE = 5

/**
 * Ada, a mascote da tela de login: um robô em SVG que reage ao formulário.
 * Decorativa (aria-hidden): as mensagens importantes, como o erro de login, são anunciadas pelo formulário.
 */
export function Mascote({ estado }: { estado: EstadoMascote }) {
  const olhos = useRef<SVGGElement>(null)

  useEffect(() => {
    const g = olhos.current
    if (!g) return
    if (estado !== 'ocioso') {
      const [x, y] = OLHAR[estado] ?? [0, 0]
      g.style.transform = `translate(${x}px, ${y}px)`
      return
    }
    // Segue o cursor escrevendo direto no style, no máximo uma vez por quadro
    let quadro = 0
    function seguir(evento: PointerEvent) {
      cancelAnimationFrame(quadro)
      quadro = requestAnimationFrame(() => {
        if (!g) return
        const caixa = g.ownerSVGElement!.getBoundingClientRect()
        const dx = evento.clientX - (caixa.left + caixa.width / 2)
        const dy = evento.clientY - (caixa.top + caixa.height / 2)
        const distancia = Math.hypot(dx, dy) || 1
        const forca = Math.min(distancia / 200, 1) * ALCANCE
        g.style.transform = `translate(${((dx / distancia) * forca).toFixed(1)}px, ${((dy / distancia) * forca).toFixed(1)}px)`
      })
    }
    g.style.transform = 'translate(0px, 0px)'
    window.addEventListener('pointermove', seguir)
    return () => {
      window.removeEventListener('pointermove', seguir)
      cancelAnimationFrame(quadro)
    }
  }, [estado])

  const fechado = estado === 'senha'
  const triste = estado === 'triste'

  return (
    <div aria-hidden className="flex items-end gap-3">
      {/* Flutua devagar (só transform); parada se o sistema pedir menos movimento */}
      <div className="shrink-0 motion-safe:animate-[flutuar_4s_ease-in-out_infinite]">
        <svg viewBox="0 0 120 120" className="size-24 overflow-visible drop-shadow-[0_10px_24px_rgba(65,105,225,0.45)]">
          <defs>
            <linearGradient id="ada-corpo" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#7ca3f5" />
              <stop offset="1" stopColor="#2b57c4" />
            </linearGradient>
          </defs>
          {/* Antena com a luz pulsando */}
          <line x1="60" y1="22" x2="60" y2="8" stroke="#7ca3f5" strokeWidth="3" strokeLinecap="round" />
          <circle
            cx="60"
            cy="7"
            r="5"
            fill={triste ? '#f87171' : '#c4d6ff'}
            className="motion-safe:animate-[pulsar_2s_ease-in-out_infinite]"
          />
          {/* Cabeça e tela do rosto */}
          <rect x="12" y="22" width="96" height="84" rx="30" fill="url(#ada-corpo)" />
          <rect x="22" y="34" width="76" height="58" rx="22" fill="#0b1224" />
          {/* Bochechas */}
          <circle cx="34" cy="76" r="5" fill="#f9a8d4" opacity={triste ? 0.15 : 0.45} />
          <circle cx="86" cy="76" r="5" fill="#f9a8d4" opacity={triste ? 0.15 : 0.45} />
          {/* Olhos: o grupo anda (olhar), cada olho fecha por scaleY (piscar, senha) */}
          <g ref={olhos} className="transition-transform duration-150 ease-saida">
            <Olho cx={46} fechado={fechado} />
            {/* Espiando: só o olho direito abre */}
            <Olho cx={74} fechado={fechado} />
          </g>
          {/* Boca */}
          <path
            d={triste ? 'M50 82 Q60 75 70 82' : estado === 'espiando' ? 'M52 79 Q60 79 68 79' : 'M50 77 Q60 86 70 77'}
            fill="none"
            stroke="#7ca3f5"
            strokeWidth="3"
            strokeLinecap="round"
            className="transition-[d] duration-200 ease-saida"
          />
          {/* Mãos tapando os olhos quando a senha está oculta; uma desce para espiar */}
          <Mao x={30} escondida={!fechado && estado !== 'espiando'} />
          <Mao x={66} escondida={!fechado} />
        </svg>
      </div>

      {/* Balão de fala: a key reinicia a entrada a cada nova fala */}
      <p
        key={estado}
        className="relative mb-6 max-w-60 rounded-2xl rounded-bl-sm border border-borda bg-superficie px-3.5 py-2.5 text-sm leading-snug font-medium text-titulo shadow-lg shadow-slate-900/10 transition-[opacity,translate] duration-200 ease-saida starting:translate-y-1 starting:opacity-0 dark:shadow-black/30"
      >
        {FALAS[estado]}
      </p>
    </div>
  )
}

function Olho({ cx, fechado }: { cx: number; fechado: boolean }) {
  return (
    <rect
      x={cx - 6}
      y={52}
      width={12}
      height={16}
      rx={6}
      fill="#9fe8ff"
      // Pisca sozinho de tempos em tempos; fechado (senha) fica como uma linha
      className={`origin-center transition-transform duration-150 ease-saida [transform-box:fill-box] ${fechado ? 'scale-y-[0.12]' : 'motion-safe:animate-[piscar_5s_infinite]'}`}
    />
  )
}

function Mao({ x, escondida }: { x: number; escondida: boolean }) {
  return (
    <rect
      x={x}
      y={46}
      width={24}
      height={26}
      rx={12}
      fill="#5b82e8"
      stroke="#0b1224"
      strokeWidth={2}
      // Sobe de baixo da cabeça para tapar o olho; volta ao esconder
      className={`transition-[translate,opacity] duration-200 ease-saida ${escondida ? 'translate-y-16 opacity-0' : 'translate-y-0 opacity-100'}`}
    />
  )
}
