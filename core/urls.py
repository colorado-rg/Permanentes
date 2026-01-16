from django.urls import path
from . import views
       
urlpatterns = [
    path('', views.home, name='home'),
    path('listagem/nova/', views.criar_listagem, name='criar_listagem'),
    path('listagem/<int:pk>/', views.detalhe_listagem, name='detalhe_listagem'),
    path('listagem/<int:pk>/imprimir/', views.imprimir_listagem, name="imprimir_listagem"),
    path('listagem/<int:pk>/editar/', views.editar_listagem, name='editar_listagem'),
    path('item/<int:item_pk>/apagar/', views.apagar_item, name='apagar_item'),
    path('verificar-em-lote/', views.verificar_lote, name='verificar_lote'),
    path('ajax/get-processos/', views.get_processos_caixa, name='get_processos_caixa'),
    path('conferir-caixa/', views.conferir_caixa, name='conferir_caixa'),
    path('ajax/checar-processo/', views.checar_processo_individual, name='checar_processo_individual'),
]