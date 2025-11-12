from django.contrib import admin
from .models import ProcessoPermanente, Listagem, ItemProcesso

@admin.register(ProcessoPermanente)
class ProcessoPermanenteAdmin(admin.ModelAdmin):
    # Campos para mostrar na listagem do admin
    list_display = ('numero', 'encontrado_por', 'data_encontrado', 'listagem_encontrado')
    # Permite procurar pelo 'numero'
    search_fields = ('numero',)
    # Adiciona um filtro para ver quais já foram encontrados
    list_filter = ('data_encontrado',)

@admin.register(Listagem)
class ListagemAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'criador', 'data_criacao')
    search_fields = ('titulo', 'criador__username')

@admin.register(ItemProcesso)
class ItemProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero_digitado', 'listagem', 'e_permanente')
    list_filter = ('e_permanente',)
    search_fields = ('numero_digitado', 'listagem__titulo')