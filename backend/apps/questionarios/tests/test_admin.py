import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.contas.models import Usuario
from apps.questionarios.admin import SEM_FATORES_AINDA
from apps.questionarios.models import Dimensao, Fator, Pergunta, Questionario


def opcoes(html, nome_do_campo):
    """Rótulos das opções de um <select> (sem a opção vazia)."""
    select = re.search(rf'<select name="{re.escape(nome_do_campo)}"[^>]*>(.*?)</select>', html, re.S)
    return re.findall(r'<option value="[^"]+"[^>]*>([^<]*)</option>', select.group(1))


class EscolhasComDuasVersoesTests(TestCase):
    """Com mais de uma versão, cada uma tem cópias próprias de dimensões e fatores com os mesmos nomes."""

    def setUp(self):
        call_command('carregar_modelo_prontidao', stdout=StringIO())
        self.v1 = Questionario.objects.get(ativo=True)
        self.v2 = self.v1.nova_versao('2.0')
        self.client.force_login(Usuario.objects.create_superuser('raiz', 'raiz@exemplo.com', 'senha-de-teste-123'))

    def pagina(self, nome_da_url, *args):
        resposta = self.client.get(reverse(nome_da_url, args=args))
        self.assertEqual(resposta.status_code, 200)
        return resposta.content.decode()

    def test_editar_pergunta_mostra_so_os_fatores_da_dimensao_dela(self):
        pergunta = Pergunta.objects.filter(dimensao__questionario=self.v2, fator__isnull=False).first()

        fatores = opcoes(self.pagina('admin:questionarios_pergunta_change', pergunta.pk), 'fator')

        esperados = Fator.objects.filter(dimensao=pergunta.dimensao)
        self.assertEqual(len(fatores), esperados.count())
        self.assertTrue(all('(v2.0)' in rotulo for rotulo in fatores))

    def test_adicionar_pergunta_lista_todos_os_fatores_sem_rotulos_repetidos(self):
        html = self.pagina('admin:questionarios_pergunta_add')

        fatores, dimensoes = opcoes(html, 'fator'), opcoes(html, 'dimensao')

        self.assertEqual(len(fatores), Fator.objects.count())
        self.assertEqual(len(fatores), len(set(fatores)))
        self.assertEqual(len(dimensoes), Dimensao.objects.count())
        self.assertEqual(len(dimensoes), len(set(dimensoes)))
        self.assertIn('Dados (v2.0)', dimensoes)

    def test_inline_de_perguntas_ao_editar_dimensao_mostra_so_os_fatores_dela(self):
        dimensao = Dimensao.objects.get(questionario=self.v1, codigo='dados')

        fatores = opcoes(self.pagina('admin:questionarios_dimensao_change', dimensao.pk), 'perguntas-0-fator')

        self.assertEqual(len(fatores), dimensao.fatores.count())

    def test_inline_de_perguntas_ao_adicionar_dimensao_nao_lista_fatores_de_outras(self):
        html = self.pagina('admin:questionarios_dimensao_add')

        self.assertEqual(opcoes(html, 'perguntas-__prefix__-fator'), [])

    def test_inline_de_perguntas_ao_adicionar_dimensao_explica_por_que_esta_vazio(self):
        html = self.pagina('admin:questionarios_dimensao_add')

        self.assertIn(SEM_FATORES_AINDA, html)
        self.assertIn('aparecem aqui depois de salvar', html)

    def test_dimensao_nova_salva_e_depois_mostra_os_proprios_fatores(self):
        dados = {
            'questionario': self.v2.pk, 'nome': 'Ética', 'codigo': '', 'descricao': '', 'peso': 1, 'ordem': 6,
            'ativa': 'on', '_continue': 'Salvar e continuar editando',
            'fatores-TOTAL_FORMS': 1, 'fatores-INITIAL_FORMS': 0,
            'fatores-0-nome': 'Transparência', 'fatores-0-codigo': '', 'fatores-0-descricao': '', 'fatores-0-ordem': 1,
            'perguntas-TOTAL_FORMS': 0, 'perguntas-INITIAL_FORMS': 0,
        }

        resposta = self.client.post(reverse('admin:questionarios_dimensao_add'), dados)

        dimensao = Dimensao.objects.get(questionario=self.v2, nome='Ética')
        self.assertRedirects(resposta, reverse('admin:questionarios_dimensao_change', args=[dimensao.pk]))
        html = self.pagina('admin:questionarios_dimensao_change', dimensao.pk)
        self.assertEqual(opcoes(html, 'perguntas-__prefix__-fator'), ['Transparência · Ética (v2.0)'])
        self.assertNotIn(SEM_FATORES_AINDA, html)
