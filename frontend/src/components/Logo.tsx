import { useId } from 'react'

/** Monograma: um "A" cujo traço do meio é um nó de IA, sobre um quadrado em degradê azul-roxo. */
export function SimboloLogo({ className = 'size-8' }: { className?: string }) {
  // id único: com duas logos na página, um <linearGradient> não "rouba" o do outro
  const gradiente = useId()
  return (
    <svg viewBox="0 0 32 32" className={`shrink-0 ${className}`} aria-hidden>
      <defs>
        <linearGradient id={gradiente} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4f7bf0" />
          <stop offset="1" stopColor="#6d4fe0" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${gradiente})`} />
      <path d="M9.5 24 L16 8 L22.5 24" fill="none" stroke="#fff" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="18.5" r="2.6" fill="#fff" />
      <path d="M12.4 18.5h-1.2M20.8 18.5h-1.2" stroke="#fff" strokeWidth={2} strokeLinecap="round" />
    </svg>
  )
}

/** Símbolo + nome: "Adoção de" e "IA" em degradê. */
export function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <SimboloLogo />
      <span className="text-base font-semibold tracking-tight whitespace-nowrap text-titulo">
        Adoção de{' '}
        <span className="bg-linear-to-r from-[#4169e1] to-[#7c5ce6] bg-clip-text font-extrabold text-transparent dark:from-[#7ca3f5] dark:to-[#a78bfa]">
          IA
        </span>
      </span>
    </span>
  )
}
