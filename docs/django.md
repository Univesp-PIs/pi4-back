# Controles basicos para Django

# Instalação
pip install django
pip install mysqlclient
pip install django djangorestframework
pip install djangorestframework-jwt
pip install python-dotenv
pip install dj-database-url
pip install psycopg2-binary

# Projetos
No terminal, digitar:
django-admin startproject nome_projeto (curriculum42)

# Aplicativos
No terminal, localizar a pasta do projeto:
    cd .\nome_projeto\ ou cd caminho_completo\nome_projeto

Depois, digitar:
    django-admin startapp nome_aplicativo (users, etc)

# Adicionar REST Framework a pasta do projeto
Na pata do projeto, abrir o arquivo settings.py

Na parte de "Application definition", ir para o "INSTALLED_APPS" e adicionar na ultima linha:
    'rest_framework,'

# Adicionar aplicativos a pasta do projeto
Na pata do projeto, abrir o arquivo settings.py

Dentro da pasta do aplicativo, terá a pasta 'apps.py' - Lá está o nome da classe de configuração que deve ser igual a digitada (primeira letra maiuscula)

Na parte de "Application definition", ir para o "INSTALLED_APPS" e adicionar na ultima linha:
    'nome_aplicativo.apps.Nome_aplicativoConfig,'

# Adicionar URLs locais no Aplicativo
Na pasta do aplicativo, criar o arquivo:
    'urls.py' - Serão as urls especificas deste aplicativo

Dentro do arquivo nome_aplicativo\urls.py, escrever:

    from django.urls import path
    from .views import nome_classe

    urlpatterns = [
        path('', nome_classe.nome_função)
    ]

    Obs.: O path('') é a parte da url que deverá ser digitada para acessar a viewer em especifico
            '' diz que não precisa acessar nada para a views do servidor

# Adicionar URLs locais no Projeto
Na pasta do projeto, abrir o arquivo 'urls.py', importar a biblioteca "include"
    'from django.urls import path, include'

Na variavel "urlpatterns", adicionar a seguinte linha:
    'path('', include('nome_aplicativo.urls')),'

# Criar MIGRATIONS
No terminal, localizar a pasta do aplicativo e digitar:
    'python .\manage.py makemigrations'

    Na primeira vez, irá criar o arquivo:
        'db.sqlite.md'

# Rodar MIGRATION
No terminal, localizar a pasta do aplicativo e digitar:
    'python .\manage.py migrate'

# Rodar o servidor
No terminal, localizar a pasta do aplicativo e digitar:
    'python .\manage.py runserver'

    Irá indicar link para o servidor atual, geralmente:
    'http://127.0.0.1:8000' - Aparece o que está na views do aplicativo