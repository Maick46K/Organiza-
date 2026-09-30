from django.urls import path

from . import views

urlpatterns = [
    path('', views.painel, name='painel'),
    path('tarefa/salvar/', views.tarefa_salvar, name='tarefa_salvar'),
    path('tarefa/<int:pk>/excluir/', views.tarefa_excluir, name='tarefa_excluir'),
    path('tarefa/<int:pk>/concluir/', views.tarefa_concluir, name='tarefa_concluir'),
    path('aula/salvar/', views.aula_salvar, name='aula_salvar'),
    path('aula/<int:pk>/excluir/', views.aula_excluir, name='aula_excluir'),
    path('calendario/', views.calendario, name='calendario'),
    path('calendario/evento/', views.evento_salvar, name='evento_salvar'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('usuarios/', views.usuarios, name='usuarios'),
]
