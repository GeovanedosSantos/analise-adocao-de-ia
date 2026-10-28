"""Prontidão, não maturidade: são conceitos diferentes. A aptidão (apta/não apta) saiu do modelo."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('avaliacoes', '0006_row_level_security_plano_de_acao'),
    ]

    operations = [
        # Renomeia em vez de recriar, para não perder o nível das avaliações já feitas
        migrations.RenameField(model_name='avaliacao', old_name='nivel_maturidade', new_name='nivel_prontidao'),
        migrations.AlterField(
            model_name='avaliacao',
            name='nivel_prontidao',
            field=models.PositiveSmallIntegerField(blank=True, help_text='De 1 a 5.', null=True),
        ),
        migrations.RemoveField(model_name='avaliacao', name='apta'),
    ]
