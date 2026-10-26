// Um único ouvinte para a página toda: posiciona a luz (index.css, .cartao) no cartão sob o cursor.
// Só em mouse/trackpad; no toque não há hover. No máximo uma escrita por quadro.
if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
  let quadro = 0
  document.addEventListener(
    'pointermove',
    (evento) => {
      const cartao = (evento.target as Element | null)?.closest?.<HTMLElement>('.cartao')
      if (!cartao) return
      cancelAnimationFrame(quadro)
      quadro = requestAnimationFrame(() => {
        const caixa = cartao.getBoundingClientRect()
        cartao.style.setProperty('--luz-x', `${evento.clientX - caixa.left}px`)
        cartao.style.setProperty('--luz-y', `${evento.clientY - caixa.top}px`)
      })
    },
    { passive: true },
  )
}
