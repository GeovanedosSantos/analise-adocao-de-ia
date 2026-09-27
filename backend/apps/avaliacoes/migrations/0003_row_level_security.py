"""Row-Level Security por empresa (RNF01, US02).

As políticas leem duas variáveis da transação, definidas em apps.contas.tenancy:
- app.empresa_id: empresa do usuário da requisição;
- app.ignorar_rls: 'on' para workers do Celery e para o painel administrativo.
Sem nenhuma das duas definida, nenhuma linha é visível. FORCE aplica as políticas também ao
dono das tabelas; só superusuários continuam ignorando RLS.
"""

from django.db import migrations

IGNORAR = "current_setting('app.ignorar_rls', true) = 'on'"
DA_EMPRESA = "empresa_id::text = current_setting('app.empresa_id', true)"
AVALIACAO_DA_EMPRESA = (
    'EXISTS (SELECT 1 FROM avaliacoes_avaliacao a '
    "WHERE a.id = avaliacao_id AND a.empresa_id::text = current_setting('app.empresa_id', true))"
)

POLITICAS = {
    'avaliacoes_avaliacao': DA_EMPRESA,
    'avaliacoes_resposta': AVALIACAO_DA_EMPRESA,
    'avaliacoes_pontuacaodimensao': AVALIACAO_DA_EMPRESA,
}


def habilitar(tabela, condicao):
    regra = f'{IGNORAR} OR {condicao}'
    return (
        f'ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;'
        f'ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;'
        f'CREATE POLICY isolamento_empresa ON {tabela} USING ({regra}) WITH CHECK ({regra});'
    )


def desabilitar(tabela):
    return (
        f'DROP POLICY IF EXISTS isolamento_empresa ON {tabela};'
        f'ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY;'
        f'ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('avaliacoes', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(habilitar(tabela, condicao), reverse_sql=desabilitar(tabela))
        for tabela, condicao in POLITICAS.items()
    ]
