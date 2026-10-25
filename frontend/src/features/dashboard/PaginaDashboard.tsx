import { Alerta } from '@/components/Alerta'
import { BotaoLink } from '@/components/Botao'

/** Tela inicial do usuário (UC04). */
export function PaginaDashboard() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <h2>Dashboard</h2>
      <Alerta titulo="Em construção">
        Aqui vão aparecer os indicadores de prontidão: o radar com a avaliação atual sobreposta à anterior, a linha do
        tempo do índice geral e os deltas entre avaliações (UC04, US07, RF12 a RF14).
      </Alerta>
      <div className="flex flex-wrap gap-3">
        <BotaoLink to="/questionario">Responder questionário</BotaoLink>
        <BotaoLink to="/resultados" variante="secundario">
          Ver último resultado
        </BotaoLink>
      </div>
    </div>
  )
}
