from django.test import SimpleTestCase

from apps.avaliacoes import graficos


class GraficosTests(SimpleTestCase):
    def test_radar_desenha_atual_e_anterior(self):
        svg = graficos.radar(['Dados', 'Pessoas', 'Tecnologia'], [25, 100, 50], [50, 50, None])

        self.assertTrue(svg.startswith('<svg'))
        self.assertEqual(svg.count(graficos.COR_ATUAL), 2)  # preenchimento e contorno
        self.assertIn(graficos.COR_ANTERIOR, svg)

    def test_radar_precisa_de_tres_eixos_e_escapa_os_nomes(self):
        self.assertEqual(graficos.radar(['A', 'B'], [1, 2]), '')
        self.assertIn('P&amp;D', graficos.radar(['P&D', 'B', 'C'], [1, 2, 3]))

    def test_linha_do_tempo_precisa_de_duas_avaliacoes(self):
        self.assertEqual(graficos.linha_do_tempo([('01/01/26', 50)]), '')
        self.assertEqual(graficos.linha_do_tempo([('01/01/26', 50), ('01/02/26', 70)]).count('<circle'), 2)
