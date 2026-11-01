'use strict';
// Botão de tema do painel com o mesmo comportamento do site (frontend/src/components/AlternarTema.tsx):
// sem escolha salva, segue o sistema (inclusive se ele mudar com a página aberta); o clique alterna
// entre claro e escuro e salva a escolha. Usa a chave "theme" do Django, que o admin/js/theme.js
// lê no <head> para aplicar o tema antes de pintar a página.
{
    const html = document.documentElement;
    const sistema = window.matchMedia('(prefers-color-scheme: dark)');

    function escuro() {
        const tema = html.dataset.theme;
        return tema === 'dark' || (tema !== 'light' && sistema.matches);
    }

    function atualizarBotoes() {
        const estaEscuro = escuro();
        const rotulo = estaEscuro ? 'Usar tema claro' : 'Usar tema escuro';
        document.querySelectorAll('.painel-tema').forEach((botao) => {
            botao.dataset.escuro = String(estaEscuro);
            botao.setAttribute('aria-label', rotulo);
            botao.title = rotulo;
        });
    }

    function alternar() {
        const novo = escuro() ? 'light' : 'dark';
        html.dataset.theme = novo;
        try {
            localStorage.setItem('theme', novo);
        } catch (erro) {
            // Sem storage: a escolha vale só até recarregar
        }
        atualizarBotoes();
    }

    document.querySelectorAll('.painel-tema').forEach((botao) => botao.addEventListener('click', alternar));
    sistema.addEventListener('change', atualizarBotoes);
    atualizarBotoes();
}
