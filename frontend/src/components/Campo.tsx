import { useId, useState, type InputHTMLAttributes, type Ref } from 'react'
import { Eye, EyeOff } from 'lucide-react'

// text-base no celular: abaixo de 16px o iOS dá zoom ao focar o campo
export const CLASSE_CAMPO =
  'h-11 w-full rounded-lg border border-borda bg-superficie px-3 text-base text-titulo placeholder:text-texto/60 shadow-xs outline-none transition-colors duration-150 focus:border-destaque focus:ring-3 focus:ring-destaque/20 aria-invalid:border-red-500 aria-invalid:focus:ring-red-500/20 sm:text-sm dark:aria-invalid:border-red-400'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'className'> & {
  rotulo: string
  /** Mensagem de erro do campo: fica logo abaixo e é lida junto com o campo por leitores de tela. */
  erro?: string
  /** Orientação curta mostrada abaixo do campo enquanto não há erro. */
  dica?: string
  ref?: Ref<HTMLInputElement>
}

/** Campo com rótulo, dica e erro associados ao input (aria-describedby / aria-invalid). */
export function Campo({ rotulo, erro, dica, id, type = 'text', ref, ...props }: Props) {
  const gerado = useId()
  const idCampo = id ?? gerado
  const idAjuda = `${idCampo}-ajuda`
  const [senhaVisivel, setSenhaVisivel] = useState(false)
  const ehSenha = type === 'password'
  const ajuda = erro ?? dica

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={idCampo} className="text-sm font-medium text-titulo">
        {rotulo}
      </label>
      <span className="relative">
        <input
          ref={ref}
          id={idCampo}
          type={ehSenha && senhaVisivel ? 'text' : type}
          aria-invalid={erro ? true : undefined}
          aria-describedby={ajuda ? idAjuda : undefined}
          className={`${CLASSE_CAMPO} ${ehSenha ? 'pr-11' : ''}`}
          {...props}
        />
        {ehSenha && (
          <button
            type="button"
            onClick={() => setSenhaVisivel((v) => !v)}
            onPointerDown={(e) => e.preventDefault()}
            aria-label={senhaVisivel ? 'Ocultar senha' : 'Mostrar senha'}
            aria-pressed={senhaVisivel}
            className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-lg text-texto hover:text-titulo focus-visible:outline-2 focus-visible:outline-destaque"
          >
            {senhaVisivel ? <EyeOff size={18} aria-hidden /> : <Eye size={18} aria-hidden />}
          </button>
        )}
      </span>
      {ajuda && (
        <p id={idAjuda} className={`text-xs ${erro ? 'font-medium text-red-700 dark:text-red-300' : 'text-texto'}`}>
          {ajuda}
        </p>
      )}
    </div>
  )
}
