import jwt
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from account.models import Credential
from .models import Project, Client, Condition, Ranking, Note, Information

from modules.mymail.mymail import MyMail

# Validar Token
@csrf_exempt
def validate_token(request):

    # Carregar token do request
    auth_header = request.headers.get('Authorization')

    # Verificar se o token está presente
    if not auth_header:
        return JsonResponse({'error': 'Token não fornecido'}, status=401)
    
    # Validar token
    try:

        # Extrai e decodifica o token do cabeçalho
        token = auth_header.split(' ')[1]
        
        # Busca no banco o usuário com esse token
        user = Credential.objects.get(token=token)
        
        # Retornar o user_id se o token for válido
        return user

    except Credential.DoesNotExist:
        return JsonResponse({'error': 'Token inválido'}, status=401)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Criar novo projeto
@csrf_exempt
def create_project(request):
    # Verifica se a requisição é do tipo POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carrega o corpo da requisição como JSON
        data = json.loads(request.body)

        # Obtém os dados enviados
        project_data = data.get('project')
        client_data = data.get('client')
        information_data = data.get('information')
        timeline = data.get('timeline')

        # Verifica se os campos obrigatórios do projeto e cliente foram preenchidos
        if not all([project_data, client_data, timeline]):
            errors = {
                'project': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not project_data else [],
                'client': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not client_data else [],
                'timeline': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not timeline else [],
            }
            return JsonResponse({'errors': errors}, status=400)

        # Verifica se as informações do projeto foram enviadas
        if not information_data:
            information_data = {}

        # Cria o projeto
        project = Project.objects.create(
            name=project_data['name'],
            key=get_random_string(length=20)
        )

        # Cria o cliente relacionado ao projeto
        client = Client.objects.create(
            project=project,
            name=client_data['name'],
            email=client_data['email']
        )

        # Cria as informações do projeto, caso sejam fornecidas
        information = Information.objects.create(
            project=project,
            cost_estimate=information_data.get('cost_estimate'),
            current_cost=information_data.get('current_cost'),
            delivered_date=information_data.get('delivered_date'),
            current_date=information_data.get('current_date')
        )

        # Cria os rankings e condições na timeline
        for timeline_item in timeline:
            ranking_data = timeline_item['ranking']
            condition_data = ranking_data['condition']

            # Verifica a ID da condição ou cria uma nova
            condition_id = condition_data.get('id', 0)

            if condition_id == 0:
                # Se a condição não existir, cria uma nova
                condition = Condition.objects.create(name=condition_data['name'])
            else:
                # Se a condição existir, busca no banco
                condition = Condition.objects.get(pk=condition_id)

            # Cria o ranking
            Ranking.objects.create(
                project=project,
                condition=condition,
                rank=ranking_data['rank'],
                last_update=ranking_data.get('last_update'),
                note=ranking_data.get('note'),
                description=ranking_data.get('description')
            )

        # Retorna mensagem de sucesso
        return JsonResponse({'message': 'Projeto criado com sucesso'})

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)


# Atualizar projeto
@csrf_exempt
def update_project(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verifica se a requisição é do tipo PUT
    if request.method != 'PUT':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carrega o corpo da requisição como JSON
        data = json.loads(request.body)

        # Obtém os dados enviados
        project_data = data.get('project')
        client_data = data.get('client')
        timeline = data.get('timeline')
        information_data = data.get('information')

        # Verifica se os campos obrigatórios foram preenchidos
        if not all([project_data, client_data, timeline, information_data]):
            errors = {
                'project': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not project_data else [],
                'client': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not client_data else [],
                'timeline': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not timeline else [],
                'information': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not information_data else [],
            }
            return JsonResponse({'errors': errors}, status=400)

        # Atualiza o projeto
        project = get_object_or_404(Project, id=project_data['id'])
        project.name = project_data['name']
        project.save()

        # Atualiza o cliente
        client = get_object_or_404(Client, project=project)
        client.name = client_data['name']
        client.email = client_data['email']
        client.save()

        # Atualiza o information
        information = get_object_or_404(Information, project=project)
        information.cost_estimate = information_data['cost_estimate']
        information.current_cost = information_data['current_cost']
        information.delivered_date = information_data['delivered_date']
        information.current_date = information_data['current_date']
        information.save()

        # Atualiza ou cria os rankings e condições na timeline
        for timeline_item in timeline:
            ranking_data = timeline_item['ranking']
            condition_data = ranking_data['condition']

            # Verifica os dados da condição e do ranking
            condition_id = condition_data.get('id', 0)
            ranking_id = ranking_data.get('id', 0)
            ranking_delete = ranking_data.get('delete', False)

            # Verifica se a condição já existe ou cria uma nova
            if condition_id == 0:
                condition = Condition.objects.create(name=condition_data['name'])
            else:
                condition = Condition.objects.get(pk=condition_id)

            # Se o ranking não existe, cria um novo
            if ranking_id == 0:
                Ranking.objects.create(
                    project=project,
                    condition=condition,
                    rank=ranking_data['rank'],
                    last_update=ranking_data.get('last_update', None),
                    note=ranking_data['note'],
                    description=ranking_data.get('description', None)
                )
            else:
                # Se o ranking foi marcado para deletar
                if ranking_delete:
                    ranking = get_object_or_404(Ranking, id=ranking_id)
                    ranking.delete()
                else:
                    # Atualiza o ranking existente
                    ranking = get_object_or_404(Ranking, id=ranking_id)
                    ranking.condition = condition
                    ranking.rank = ranking_data['rank']
                    ranking.last_update = ranking_data['last_update']
                    ranking.note = ranking_data['note']
                    ranking.description = ranking_data.get('description', None)
                    ranking.save()

        # Retorna uma resposta de sucesso
        return JsonResponse({'message': 'Projeto atualizado com sucesso'}, status=200)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)


# Deletar projeto
@csrf_exempt
def delete_project(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verifica se a requisição é do tipo DELETE
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Obtém o ID do projeto a ser deletado via parâmetros da URL
        project_id = request.GET.get('id')

        # Verifica se o ID foi fornecido
        if not project_id:
            return JsonResponse({'error': 'Parâmetro "id" é obrigatório'}, status=400)

        # Busca o projeto pelo ID ou retorna 404 se não encontrado
        project = get_object_or_404(Project, id=project_id)

        # Deleta o projeto (o Django vai automaticamente deletar os relacionados)
        project.delete()

        # Retorna uma resposta de sucesso
        return JsonResponse({'message': 'Projeto e dados relacionados deletados com sucesso'}, status=200)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)

# Informações do projeto
@csrf_exempt
def info_project(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Definir metodo
    if request.method == 'GET':

        try:

            # Buscar parametros na url
            id = request.GET.get('id', None)

            # Buscar o projeto pelo ID
            project = get_object_or_404(Project, id=id)

            # Buscar o cliente associado ao projeto
            client = get_object_or_404(Client, project=project)

            # Buscar o ranking associado ao projeto
            rankings = Ranking.objects.filter(project=project)

            # Cria lista para timeline
            timeline = []

            # Preenche a lista da timeline com dados dos rankings
            for ranking in rankings:

                # Adiciona dados ao timeline
                timeline.append({
                    'ranking': {
                        'id': ranking.id,
                        'rank': ranking.rank,
                        'last_update': ranking.last_update,
                        'note': ranking.note,
                        'description': ranking.description,
                        'condition': {
                            'id': ranking.condition.id,
                            'name': ranking.condition.name
                        }
                    }
                })

            # Montar o objeto de resposta com dados do projeto, cliente e timeline
            response_data = {
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'key': project.key
                },
                'client': {
                    'id': client.id,
                    'name': client.name,
                    'email': client.email
                },
                'timeline': timeline
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


# Listar todos os projetos
@csrf_exempt
def list_project(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é GET
    if request.method == 'GET':

        try:
            # Buscar todos os projetos
            projects = Project.objects.all()

            # Criar uma lista para armazenar os dados dos projetos
            project_list = []
            
            # Iterar sobre cada projeto e montar o JSON de resposta
            for project in projects:

                # Buscar o cliente associado ao projeto
                client = get_object_or_404(Client, project=project)

                # Buscar o ranking associado ao projeto
                rankings = Ranking.objects.filter(project=project)

                # Criar uma lista para armazenar os dados dos projetos
                timeline = []

                # Preenche a lista da timeline com dados dos rankings
                for ranking in rankings:

                    # Adiciona dados ao timeline
                    timeline.append({
                        'ranking': {
                            'id': ranking.id,
                            'rank': ranking.rank,
                            'last_update': ranking.last_update,
                            'note': ranking.note,
                            'description': ranking.description,
                            'condition': {
                                'id': ranking.condition.id,
                                'name': ranking.condition.name
                            }
                        }
                    })

                # Montar o objeto de resposta com dados do projeto, cliente e timeline
                project_data = {
                    'project': {
                        'id': project.id,
                        'name': project.name,
                        'key': project.key
                    },
                    'client': {

                        'id': client.id,
                        'name': client.name,
                        'email': client.email
                    },
                    'timeline': timeline
                }

                # Limpar timeline para o próximo projeto
                project_list.append(project_data)

            # Retornar a lista de projetos em formato JSON
            return JsonResponse(project_list, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Buscar informações do projeto
@csrf_exempt
def search_project(request):

    # Definir metodo
    if request.method == 'GET':

        try:

            # Buscar parametros na url
            key = request.GET.get('key', None)

            # Buscar o projeto com base no campo fornecido
            project = get_object_or_404(Project, key=key)

            # Buscar o cliente associado ao projeto
            client = get_object_or_404(Client, project=project)

            # Buscar o ranking associado ao projeto
            rankings = Ranking.objects.filter(project=project)

            # Cria lista para timeline
            timeline = []

            # Preenche a lista da timeline com dados dos rankings
            for ranking in rankings:

                # Adiciona dados ao timeline
                timeline.append({
                    'ranking': {
                        'id': ranking.id,
                        'rank': ranking.rank,
                        'last_update': ranking.last_update,
                        'note': ranking.note,
                        'description': ranking.description,
                        'condition': {
                            'id': ranking.condition.id,
                            'name': ranking.condition.name
                        }
                    }
                })

            # Montar o objeto de resposta com dados do projeto, cliente e timeline
            response_data = {
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'key': project.key
                },
                'client': {
                    'id': client.id,
                    'name': client.name,
                    'email': client.email
                },
                'timeline': timeline
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# --------------------------------------------------------------- CONDITION ---------------------------------------------------------------

# Create Condition
@csrf_exempt
def create_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é POST
    if request.method == 'POST':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Criar uma nova condição
            condition = Condition.objects.create(
                name=data['name']
            )

            # Resposta de sucesso
            response_data = {
                'message': 'Condição criada com sucesso',
                'condition': {
                    'id': condition.id,
                    'name': condition.name
                }
            }

            return JsonResponse(response_data, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Update Condition
@csrf_exempt
def update_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é PUT
    if request.method == 'PUT':

        try:
            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Buscar a condição pelo ID
            condition = get_object_or_404(Condition, id=data['id'])

            # Atualizar os dados da condição
            condition.name = data['name']
            condition.status = data['status']
            condition.save()

            # Resposta de sucesso
            response_data = {
                'message': 'Condição atualizada com sucesso',
                'condition': {
                    'id': condition.id,
                    'name': condition.name,
                    'status': condition.status
                }
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Delete Condition
@csrf_exempt
def delete_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é DELETE
    if request.method == 'DELETE':

        try:
            # Buscar parametros na url
            id = request.GET.get('id', None)

            # Buscar a condição pelo ID
            condition = get_object_or_404(Condition, id=id)

            # Deletar a condição
            condition.delete()

            # Resposta de sucesso
            response_data = {
                'message': 'Condição deletada com sucesso'
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Desabilitar Condition
@csrf_exempt
def disable_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é PATH
    if request.method == 'PATCH':

        try:

            # Buscar parametros na url
            id = request.GET.get('id', None)

            # Buscar a condição pelo ID
            condition = get_object_or_404(Condition, id=id)

            # Alterar o status para False
            condition.status = False
            condition.save()

            # Resposta de sucesso
            response_data = {
                'message': 'Condição desabilitada com sucesso'
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Altera o Status atual da Condition
@csrf_exempt
def toggle_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é PATH
    if request.method == 'PATCH':

        try:

            # Buscar parametros na url
            id = request.GET.get('id', None)

            # Buscar a condição pelo ID
            condition = get_object_or_404(Condition, id=id)

            # Alternar o valor do status
            condition.status = not condition.status
            condition.save()

            # Resposta de sucesso
            response_data = {
                'message': 'Status da condição alternado com sucesso',
                'new_status': condition.status
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# List Condition
@csrf_exempt
def list_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verificar se o método é GET
    if request.method == 'GET':

        try:

            # Buscar todas as condições
            conditions = Condition.objects.all()

            # Criar uma lista para armazenar os dados das condições
            condition_list = []

            # Iterar sobre cada condição e montar o JSON de resposta
            for condition in conditions:
                condition_data = {
                    'id': condition.id,
                    'name': condition.name,
                    'status': condition.status
                }
                condition_list.append(condition_data)

            # Retornar a lista de condições em formato JSON
            return JsonResponse(condition_list, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# --------------------------------------------------------------- Note ---------------------------------------------------------------

@csrf_exempt
def create_note(request):

    # Verificar se o método é POST
    if request.method == 'POST':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Criar uma nova condição
            note = Note.objects.create(
                name=data['name']
            )

            # Resposta de sucesso
            response_data = {
                'message': 'Condição criada com sucesso',
                'note': {
                    'id': note.id,
                    'name': note.name
                }
            }

            return JsonResponse(response_data, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Delete Note
@csrf_exempt
def delete_note(request):

    # Verificar se o método é DELETE
    if request.method == 'DELETE':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Buscar a condição pelo ID
            note = get_object_or_404(Note, id=data['id'])

            # Deletar a condição
            note.delete()

            # Resposta de sucesso
            response_data = {
                'message': 'nota deletada com sucesso!'
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

# Edit Note
@csrf_exempt
def edit_note(request):

    # Verificar se o método é PUT
    if request.method == 'PUT':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Buscar a condição pelo ID
            note = get_object_or_404(Note, id=data['id'])
            newNote = data['note']
            note.name = newNote
            # Editar a condição
            note.save()

            # Resposta de sucesso
            response_data = {
                'message': 'nota editada com sucesso!'
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=406)

# --------------------------------------------------------------- MAIL ---------------------------------------------------------------

# Send Mail
@csrf_exempt
def send_mail(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verificar se o método é POST
    if request.method == 'POST':

        try:
            # Carregar dados do JSON
            data = json.loads(request.body.decode('utf-8'))

            # Extrair dados necessários
            type = data['type']
            login = data['login']
            password = data['password']
            recipient = data['recipient']
            subject = data['subject']
            body = data['body']

            # Criar instância do MyMail e enviar e-mail
            mailer = MyMail()
            result = mailer.mail(type, login, password, recipient, subject, body)

            if result['status']:
                return JsonResponse({'message': 'E-mail enviado com sucesso!'}, status=200)
            
            else:
                # Retorna o erro do MyMail
                return JsonResponse({'error': result.get('error', 'Falha ao enviar o e-mail.')}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)
