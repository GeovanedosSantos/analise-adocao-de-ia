import { useId } from 'react'
import { Campo } from '@/components/Campo'
import { SETORES } from './validacao'

/** Setor da empresa: texto livre com sugestões (datalist), para não travar quem não se encaixa na lista. */
export function CampoSetor({ valor, aoAlterar, erro }: { valor: string; aoAlterar: (valor: string) => void; erro?: string }) {
  const lista = useId()
  return (
    <>
      <Campo
        rotulo="Setor"
        value={valor}
        onChange={(e) => aoAlterar(e.target.value)}
        erro={erro}
        dica="Escolha uma sugestão ou escreva o setor."
        list={lista}
        maxLength={100}
        required
      />
      <datalist id={lista}>
        {SETORES.map((setor) => (
          <option key={setor} value={setor} />
        ))}
      </datalist>
    </>
  )
}
