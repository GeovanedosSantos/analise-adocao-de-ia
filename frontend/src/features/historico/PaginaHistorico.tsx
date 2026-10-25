import { Alerta } from '@/components/Alerta'

export function PaginaHistorico() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <h2>Histórico</h2>
      <Alerta titulo="Em construção">
        Aqui vão aparecer as avaliações da empresa por data, com a versão do questionário e a pontuação de cada uma,
        o link para o resultado e a comparação lado a lado (UC05, RF11).
      </Alerta>
    </div>
  )
}
