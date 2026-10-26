import { Alerta } from '@/components/Alerta'
import { Pagina } from '@/components/Pagina'

export function PaginaCatalogo() {
  return (
    <Pagina titulo="Catálogo de recomendações" descricao="Ações sugeridas para cada dimensão e faixa de pontuação.">
      <Alerta titulo="Em construção">
        Aqui vão aparecer todas as recomendações cadastradas, agrupadas por dimensão, com os detalhes de cada uma (UC06,
        RF10).
      </Alerta>
    </Pagina>
  )
}
