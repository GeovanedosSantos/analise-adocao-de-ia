from django.contrib import admin, messages

from .models import Dimensao, Fator, Pergunta, Questionario

SEM_FATORES_AINDA = 'Salve a dimensão para escolher o fator'


def _rotulo_dimensao(dimensao):
    return f'{dimensao.nome} (v{dimensao.questionario.versao})'


def _rotulo_fator(fator):
    return f'{fator.nome} · {_rotulo_dimensao(fator.dimensao)}'


class EscolhasComVersaoMixin:
    """Cada versão tem cópias próprias de dimensões e fatores, com os mesmos nomes.

    Nos selects, o rótulo leva a dimensão e a versão para que as cópias não pareçam duplicadas.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'dimensao':
            kwargs.setdefault('queryset', Dimensao.objects.select_related('questionario'))
        elif db_field.name == 'fator':
            kwargs.setdefault('queryset', Fator.objects.select_related('dimensao__questionario'))
        campo = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'dimensao':
            campo.label_from_instance = _rotulo_dimensao
        elif db_field.name == 'fator':
            campo.label_from_instance = _rotulo_fator
        return campo


class DimensaoInline(admin.TabularInline):
    model = Dimensao
    extra = 0


class FatorInline(admin.TabularInline):
    model = Fator
    extra = 0


class PerguntaInline(EscolhasComVersaoMixin, admin.TabularInline):
    model = Pergunta
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'fator':
            # Só os fatores da dimensão em edição
            object_id = request.resolver_match.kwargs.get('object_id')
            kwargs['queryset'] = Fator.objects.select_related('dimensao__questionario').filter(dimensao_id=object_id)
            if not object_id:
                # Dimensão nova: os fatores do inline acima só existem depois de salvar
                kwargs['empty_label'] = SEM_FATORES_AINDA
                kwargs['help_text'] = (
                    'Os fatores desta dimensão aparecem aqui depois de salvar. '
                    'Use "Salvar e continuar editando" e depois escolha o fator de cada pergunta.'
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ['versao', 'ativo', 'data_criacao']
    readonly_fields = ['ativo']
    inlines = [DimensaoInline]
    actions = ['publicar']

    @admin.action(description='Publicar a versão selecionada (arquiva a atual)')
    def publicar(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Selecione exatamente uma versão.', messages.ERROR)
            return
        questionario = queryset.get()
        questionario.publicar()
        self.message_user(request, f'Versão {questionario.versao} publicada.')


@admin.register(Dimensao)
class DimensaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'questionario', 'peso', 'ordem', 'ativa']
    list_filter = ['questionario', 'ativa']
    inlines = [FatorInline, PerguntaInline]


@admin.register(Pergunta)
class PerguntaAdmin(EscolhasComVersaoMixin, admin.ModelAdmin):
    list_display = ['texto', 'dimensao', 'fator', 'tipo', 'peso', 'invertida', 'ativa']
    list_filter = ['dimensao__questionario', 'tipo', 'invertida', 'ativa']
    list_editable = ['ativa']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        object_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == 'fator' and object_id:
            # Na edição, só os fatores da dimensão da pergunta
            dimensao_id = Pergunta.objects.filter(pk=object_id).values('dimensao_id')
            kwargs['queryset'] = Fator.objects.select_related('dimensao__questionario').filter(
                dimensao_id__in=dimensao_id,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
