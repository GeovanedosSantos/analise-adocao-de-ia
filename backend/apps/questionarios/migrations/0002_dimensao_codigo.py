from django.db import migrations, models
from django.utils.text import slugify


def preencher_codigos(apps, schema_editor):
    """Gera o código das dimensões existentes a partir do nome, sem repetir dentro da mesma versão."""
    Dimensao = apps.get_model('questionarios', 'Dimensao')
    usados = set()
    for dimensao in Dimensao.objects.order_by('questionario_id', 'ordem', 'nome'):
        base = slugify(dimensao.nome)[:45] or 'dimensao'
        codigo, sufixo = base, 2
        while (dimensao.questionario_id, codigo) in usados:
            codigo, sufixo = f'{base}-{sufixo}', sufixo + 1
        usados.add((dimensao.questionario_id, codigo))
        Dimensao.objects.filter(pk=dimensao.pk).update(codigo=codigo)


class Migration(migrations.Migration):

    dependencies = [
        ('questionarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dimensao',
            name='codigo',
            field=models.SlugField(
                blank=True, default='', max_length=50,
                help_text='Identificador estável entre versões (ex.: "dados"). Liga avaliações de versões diferentes '
                          'e o catálogo de recomendações. Se ficar em branco, é gerado a partir do nome.',
            ),
            preserve_default=False,
        ),
        migrations.RunPython(preencher_codigos, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='dimensao',
            constraint=models.UniqueConstraint(fields=('questionario', 'codigo'), name='dimensao_codigo_unico_na_versao'),
        ),
    ]
