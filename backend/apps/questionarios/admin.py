from django.contrib import admin, messages

from .models import Dimensao, Pergunta, Questionario


class DimensaoInline(admin.TabularInline):
    model = Dimensao
    extra = 0


class PerguntaInline(admin.TabularInline):
    model = Pergunta
    extra = 0


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
    list_display = ['nome', 'questionario', 'peso', 'ordem']
    list_filter = ['questionario']
    inlines = [PerguntaInline]


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'dimensao', 'tipo', 'peso', 'ativa']
    list_filter = ['dimensao__questionario', 'tipo', 'ativa']
    list_editable = ['ativa']
