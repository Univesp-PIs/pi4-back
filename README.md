Este é o frontend do sistema EngSol, desenvolvido em Next.js e React, para gestão de projetos de engenharia e acompanhamento de pedidos de clientes.

![image](https://github.com/user-attachments/assets/79db3e09-faaf-4a37-b81e-6ae26592dadc)

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Como Rodar o Projeto](#como-rodar-o-projeto)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Scripts Disponíveis](#scripts-disponíveis)
- [Padrões e Convenções](#padrões-e-convenções)
- [Contato](#contato)

---

## Sobre o Projeto

O **EngSol** é um sistema web para gerenciamento de projetos de engenharia, permitindo que administradores cadastrem, editem e acompanhem projetos, enquanto clientes podem consultar o andamento de seus pedidos através de uma chave de acesso.

## Funcionalidades

- **Área do Administrador**
  - Dashboard com indicadores de projetos, custos e entregas.
  - Cadastro, edição e exclusão de projetos.
  - Gerenciamento de etapas e status dos projetos.
  - Criação de contas de administradores.
  - Visualização e ordenação de projetos.

- **Área do Cliente**
  - Consulta de pedidos por chave de acesso.
  - Visualização do progresso do projeto em formato de timeline.

- **Geral**
  - Interface responsiva.
  - Autenticação e autorização de administradores.

## Tecnologias Utilizadas

- [Python](https://www.python.org)
- [Django](https://www.djangoproject.com)

## Como Rodar o Projeto

1. **Clone o repositório:**
   ```sh
   git clone https://github.com/Univesp-PIs/pi4-back.git
   cd pi4-back
   ```

2. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   - Crie um arquivo `.venv` na raiz do projeto e instale os requisitos necessários.

4. **Inicie o servidor de desenvolvimento:**
   ```sh
   cd src
   python manage.py runserver
   ```

5. **Acesse no navegador:**
   ```
   http://localhost:3000
   ```

## Estrutura de Pastas

```
src/
  src/                # Configurações do projeto
  home/               # Aplicativo da pagina inicial
  engsol/             # Aplicativo da pagina do projeto
```

## Scripts Disponíveis

- `runserver`: Inicia o servidor de desenvolvimento.

Exemplo:
```
cd src
python manage.py runserver
```

## Padrões e Convenções

- **Tipagem**: Uso de Python para segurança de tipos.
- **API**: Comunicação via JsonRequest.

## Contato

Dúvidas ou sugestões? Entre em contato pelo [e-mail](mailto:brenno_brossi_work@outlook.com) ou abra uma issue neste repositório.

---
> Projeto desenvolvido para fins acadêmicos e demonstração de habilidades em frontend.

