import jwt
import json
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.test import RequestFactory
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.db.models import Count
from django.db.models.functions import ExtractMonth

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
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

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
            start_date=datetime.strptime(information_data.get('start_date'), "%d/%m/%Y").date(),
            delivered_date=datetime.strptime(information_data.get('delivered_date'), "%d/%m/%Y").date(),
            current_date=datetime.strptime(information_data.get('current_date'), "%d/%m/%Y").date()
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
                #last_update=ranking_data.get('last_update'),
                last_update=datetime.strptime(ranking_data.get('last_update'), "%d/%m/%Y").date(),
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
        information.start_date = datetime.strptime(information_data['start_date'], "%d/%m/%Y").date()
        information.delivered_date = datetime.strptime(information_data['delivered_date'], "%d/%m/%Y").date()
        information.current_date = datetime.strptime(information_data['current_date'], "%d/%m/%Y").date()
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
                    #last_update=ranking_data.get('last_update', None),
                    last_update=datetime.strptime(ranking_data.get('last_update', None), "%d/%m/%Y").date(),
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
                    #ranking.last_update = ranking_data['last_update']
                    ranking.last_update = datetime.strptime(ranking_data['last_update'], "%d/%m/%Y").date()
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
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Obtém o ID do projeto via parâmetros da URL
        project_id = request.GET.get('id')

        # Verifica se o ID foi fornecido
        if not project_id:
            return JsonResponse({'error': 'Parâmetro "id" é obrigatório'}, status=400)

        # Busca o projeto pelo ID
        project = get_object_or_404(Project, id=project_id)

        # Busca o cliente relacionado ao projeto
        client = get_object_or_404(Client, project=project)

        # Busca as informações adicionais (se existirem)
        information = Information.objects.filter(project=project).first()

        # Busca todos os rankings do projeto
        rankings = Ranking.objects.filter(project=project)

        # Cria a timeline com os dados dos rankings
        timeline = []
        days = []
        for ranking in rankings:
            days.append(ranking.last_update)
            timeline.append({
                'ranking': {
                    'id': ranking.id,
                    'rank': ranking.rank,
                    'last_update': (ranking.last_update).strftime("%d/%m/%Y"),
                    'note': ranking.note,
                    'description': ranking.description,
                    'condition': {
                        'id': ranking.condition.id,
                        'name': ranking.condition.name
                    }
                }
            })

        # Calcular a média de dias entre etapas
        intervals = []
        for i in range(1, len(days)):
            diff = (days[i] - days[i - 1]).days
            intervals.append(diff)

        average_days = round(sum(intervals) / len(intervals), 2) if intervals else 0

        # Monta o objeto de resposta com dados do projeto, cliente, informações e timeline
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
            'information': {
                'id': information.id ,
                'cost_estimate': information.cost_estimate,
                'current_cost': information.current_cost,
                'start_date': (information.start_date).strftime("%d/%m/%Y"),
                'delivered_date': (information.delivered_date).strftime("%d/%m/%Y"),
                'current_date': (information.current_date).strftime("%d/%m/%Y")
            },
            'average_time': {
                'ranking': average_days
            },
            'timeline': timeline
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)

# Listar todos os projetos
@csrf_exempt
def list_project(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Busca todos os projetos
        projects = Project.objects.filter(status=True)

        # Lista de retorno
        project_list = []

        # Itera sobre cada projeto
        for project in projects:
            # Busca o cliente relacionado ao projeto
            client = get_object_or_404(Client, project=project)

            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()

            # Busca os rankings do projeto
            rankings = Ranking.objects.filter(project=project)

            # Monta a timeline com os rankings
            timeline = []
            for ranking in rankings:
                timeline.append({
                    'ranking': {
                        'id': ranking.id,
                        'rank': ranking.rank,
                        'last_update': (ranking.last_update).strftime("%d/%m/%Y"),
                        'note': ranking.note,
                        'description': ranking.description,
                        'condition': {
                            'id': ranking.condition.id,
                            'name': ranking.condition.name
                        }
                    }
                })

            # Monta os dados do projeto
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
                'information': {
                    'id': information.id,
                    'cost_estimate': information.cost_estimate,
                    'current_cost': information.current_cost,
                    'start_date': (information.start_date).strftime("%d/%m/%Y"),
                    'delivered_date': (information.delivered_date).strftime("%d/%m/%Y"),
                    'current_date': (information.current_date).strftime("%d/%m/%Y")
                },
                'timeline': timeline
            }

            # Adiciona o projeto na lista de resposta
            project_list.append(project_data)

        # Retorna todos os projetos encontrados
        return JsonResponse(project_list, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Buscar informações do projeto
@csrf_exempt
def search_project(request):
    # Verifica se o método é GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Buscar o parâmetro na URL
        key = request.GET.get('key', None)

        # Buscar o projeto com base na chave fornecida
        project = get_object_or_404(Project, key=key)

        # Buscar cliente associado
        client = get_object_or_404(Client, project=project)

        # Buscar informações adicionais, se existirem
        information = Information.objects.filter(project=project).first()

        # Buscar rankings associados ao projeto
        rankings = Ranking.objects.filter(project=project)

        # Construir timeline
        timeline = []
        for ranking in rankings:
            timeline.append({
                'ranking': {
                    'id': ranking.id,
                    'rank': ranking.rank,
                    'last_update': (ranking.last_update).strftime("%d/%m/%Y"),
                    'note': ranking.note,
                    'description': ranking.description,
                    'condition': {
                        'id': ranking.condition.id,
                        'name': ranking.condition.name
                    }
                }
            })

        # Construir resposta
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
            'information': {
                'id': information.id,
                'cost_estimate': information.cost_estimate,
                'current_cost': information.current_cost,
                'start_date': (information.start_date).strftime("%d/%m/%Y"),
                'delivered_date': (information.delivered_date).strftime("%d/%m/%Y"),
                'current_date': (information.current_date).strftime("%d/%m/%Y")
            },
            'timeline': timeline
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --------------------------------------------------------------- CONDITION ---------------------------------------------------------------

# Create Condition
@csrf_exempt
def create_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Update Condition
@csrf_exempt
def update_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é PUT
    if request.method != 'PUT':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Delete Condition
@csrf_exempt
def delete_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é DELETE
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Desabilitar Condition
@csrf_exempt
def disable_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é PATCH
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Altera o Status atual da Condition
@csrf_exempt
def toggle_condition(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Verifica se o método é PATCH
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# List Condition
@csrf_exempt
def list_condition(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# --------------------------------------------------------------- Note ---------------------------------------------------------------

@csrf_exempt
def create_note(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Delete Note
@csrf_exempt
def delete_note(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é DELETE
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# Edit Note
@csrf_exempt
def edit_note(request):
    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
    
    # Verifica se o método é PUT
    if request.method != 'PUT':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

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

# --------------------------------------------------------------- DASHBOARD ---------------------------------------------------------------

# Chamar todos os dashboards
@csrf_exempt
def dashboard(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carregar dados do json
        data = json.loads(request.body.decode('utf-8'))

        # Função auxiliar para simular request POST com body específico
        def make_request_for(view_func, partial_data):
            req = RequestFactory().get('/')
            req._body = json.dumps(partial_data).encode('utf-8')
            return json.loads(view_func(req).content)

        # Chama cada função com o corpo adequado
        result_delivery_projects = make_request_for(delivery_projects, {'delivery_projects': data.get('delivery_projects', {})})
        result_cost = make_request_for(cost, {'cost': data.get('cost', {})})
        result_percentage_project_cost = make_request_for(percentage_project_cost, {'cost': data.get('cost', {})})
        result_average_project_cost = make_request_for(average_project_cost, {'cost': data.get('cost', {})})
        result_average_time_project = make_request_for(average_time_project, {'cost': data.get('cost', {})})
        result_percentage_projects_delivered = make_request_for(percentage_projects_delivered, {'delivery_projects': data.get('delivery_projects', {})})
    
        # Monta o objeto de resposta com dados do projeto
        response_data = {
            'title': 'Dashboard',
            'delivery_projects': result_delivery_projects,
            'cost': result_cost,
            'percentage_project_cost': result_percentage_project_cost,
            'average_project_cost': result_average_project_cost,
            'average_time_project': result_average_time_project,
            'percentage_projects_delivered': result_percentage_projects_delivered
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)

# Projetos entregues
@csrf_exempt
def delivery_projects(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carregar dados do json
        data = json.loads(request.body.decode('utf-8'))

        # Busca as informações adicionais
        information = Information.objects.filter(delivered_date__year=data['delivery_projects']['year'])

        # Extrai o mês da delivered_date
        infos_by_month = information.annotate(
            month=ExtractMonth('delivered_date')
        ).values('month').annotate(
            count=Count('project', distinct=True)
        ).order_by('month')
        
        # Monta o objeto de resposta com dados do projeto, cliente, informações e timeline
        response_data = {
            'title': 'Projetos entregues',
            'data': [
                {"month": item['month'], "count": item['count']}
                for item in infos_by_month
            ]
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Custo estimado x real
@csrf_exempt
def cost(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carregar dados do json
        data = json.loads(request.body.decode('utf-8'))

        # Buscar ids
        costs = []
        for id_count in data['cost']['id']:

            # Busca o projeto pelo ID
            project = get_object_or_404(Project, id=id_count)

            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()

            costs.append({
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'key': project.key
                },
                'information':{
                    'cost_estimate': information.cost_estimate,
                    'current_cost': information.current_cost,
                }
            })
        
        # Monta o objeto de resposta com dados do projeto
        response_data = {
            'title': 'Estimado x Custo',
            'data': [costs]
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Projetos dentro do prazo
@csrf_exempt
def percentage_project_cost(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Busca todos os projetos
        projects = Project.objects.filter(status=True)

        # Contadores de projetos
        total = 0
        dentro_do_custo = 0

        # Itera sobre cada projeto
        for project in projects:
            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()

            # Verifica se os dados de custo estão disponíveis
            if information and information.cost_estimate is not None and information.current_cost is not None:
                total += 1

                # Verifica se o custo atual está dentro ou igual ao estimado
                if information.current_cost <= information.cost_estimate:
                    dentro_do_custo += 1

        # Calcula a porcentagem de projetos dentro do custo
        percentage = round((dentro_do_custo / total) * 100, 2) if total > 0 else 0

        # Monta o objeto de resposta com os dados calculados
        response_data = {
            'title': 'Projetos dentro do custo',
            'value': percentage
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Custo médio de um projeto
@csrf_exempt
def average_project_cost(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Busca todos os projetos
        projects = Project.objects.filter(status=True)

        # Conta de retorno
        estimate_cost = 0
        current_cost = 0
        count = 0

        # Itera sobre cada projeto
        for project in projects:

            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()
            estimate_cost += information.cost_estimate
            current_cost += information.current_cost
            count += 1
        
        average_estimate_cost = round(estimate_cost / count, 2) if count > 0 else 0
        average_current_cost = round(current_cost / count, 2) if count > 0 else 0

        # Monta o objeto de resposta com dados do projeto
        response_data = {
            'title': 'Custo médio de um projeto',
            'value': {
                'estimate_cost': average_estimate_cost,
                'current_cost': average_current_cost
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Tempo médio para finalizar projeto
@csrf_exempt
def average_time_project(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Busca todos os projetos
        projects = Project.objects.filter(status=True)

        # Conta de retorno
        estimate = 0
        current = 0
        count = 0

        # Itera sobre cada projeto
        for project in projects:

            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()
            estimate += (information.delivered_date - information.start_date).days
            current += (information.current_date - information.start_date).days
            count += 1
        
        average_estimate = round(estimate / count, 2) if count > 0 else 0
        average_current = round(current / count, 2) if count > 0 else 0

        # Monta o objeto de resposta com dados do projeto
        response_data = {
            'title': 'Tempo médio para finalizar um projeto',
            'value': {
                'estimate_days': average_estimate,
                'current_days': average_current
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Porcentagem de projetos entregues
@csrf_exempt
def percentage_projects_delivered(request):
    # Verifica se a requisição é do tipo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Busca todos os projetos
        projects = Project.objects.filter(status=True)

        # Variáveis de controle
        total_projects = len(projects)  # Total de projetos
        delivered_on_time = 0  # Projetos entregues no prazo

        # Itera sobre cada projeto
        for project in projects:
            # Busca as informações adicionais (se existirem)
            information = Information.objects.filter(project=project).first()

            # Verifica se as informações existem
            if information and information.start_date and information.delivered_date and information.current_date:
                # Calcula os dias para a entrega
                delivered_days = (information.delivered_date - information.start_date).days
                current_days = (information.current_date - information.start_date).days

                # Verifica se o projeto foi entregue dentro do prazo
                if current_days <= delivered_days:
                    delivered_on_time += 1  # Aumenta o contador de entregas no prazo

        # Calcula o percentual de projetos entregues no prazo
        percentage = (delivered_on_time / total_projects) * 100 if total_projects > 0 else 0

        # Monta o objeto de resposta com dados do projeto
        response_data = {
            'title': 'Projetos entregues no prazo',
            'value': round(percentage, 2)
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)

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
