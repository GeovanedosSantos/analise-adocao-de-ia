from django.contrib import admin, messages

from .models import Dimensao, Fator, Pergunta, Questionario


class DimensaoInline(admin.TabularInline):
    model = Dimensao
    extra = 0


class FatorInline(admin.TabularInline):
    model = Fator
    extra = 0


class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Só os fatores da dimensão em edição
        if db_field.name == 'fator' and request.resolver_match.kwargs.get('object_id'):
            kwargs['queryset'] = Fator.objects.filter(dimensao_id=request.resolver_match.kwargs['object_id'])
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
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'dimensao', 'fator', 'tipo', 'peso', 'ativa']
    list_filter = ['dimensao__questionario', 'tipo', 'ativa']
    list_editable = ['ativa']
