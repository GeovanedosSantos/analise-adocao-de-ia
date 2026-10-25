import { Alerta } from '@/components/Alerta'

export function PaginaCatalogo() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <h2>Catálogo de recomendações</h2>
      <Alerta titulo="Em construção">
        Aqui vão aparecer todas as recomendações cadastradas, agrupadas por dimensão, com os detalhes de cada uma (UC06,
        RF10).
      </Alerta>
    </div>
  )
}
