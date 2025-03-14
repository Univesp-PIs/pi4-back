# venv

# Realizar a criação do ambiente virtual (venv) seguindo os seguintes passos:

1) Abrir o menu 'Iniciar' do Windows;

2) Digitar 'Executar' na barra de pesquisa;

3) No executar, digitar 'cmd' para abrir o terminal do Windows;

4) No terminal, digitar 'cd ' e o local da pasta onde deseja criar o novo ambiente virtual;

5) No terminal, digitar 'python -m venv .venv' para criar o novo ambiente virtual;


# Para ativar a venv:

1) No terminal, digitar 'cd ' e o local da pasta onde deseja criar o novo ambiente virtual;
    
2) No terminal, digitar '.venv\Scripts\activate' para ativar o novo ambiente virtual;


# Para baixar os requisitos do novo ambiente virtual:

1) No terminal, com a venv ativada, digitar 'pip freeze > requirements.txt' para gerar o arquivos com os requisitos da venv;


# Para instalar os requisitos no novo ambiente virtual:

1) No terminal, com a venv ativada, digitar 'pip install -r requirements.txt' para instalar o arquivos dos requisitos da venv;