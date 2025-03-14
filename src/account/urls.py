# Criar um arquivo igual o 'urls.py' do projeto
from django.urls import path
from . import views

urlpatterns = [
    
    # urls padrão = localhost:8000/nome_aplicativo/nome_views
    # Importar as funções das views

    # Login
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
]