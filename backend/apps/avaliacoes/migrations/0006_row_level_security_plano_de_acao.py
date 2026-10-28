"""Row-Level Security do plano de ação, com a mesma regra das outras tabelas da avaliação (0003)."""

import importlib

from django.db import migrations

rls = importlib.import_module('apps.avaliacoes.migrations.0003_row_level_security')

TABELA = 'avaliacoes_recomendacaoavaliacao'


class Migration(migrations.Migration):
    dependencies = [
        ('avaliacoes', '0005_plano_de_acao_e_deltas_derivados'),
    ]

    operations = [
        migrations.RunSQL(rls.habilitar(TABELA, rls.AVALIACAO_DA_EMPRESA), reverse_sql=rls.desabilitar(TABELA)),
    ]
