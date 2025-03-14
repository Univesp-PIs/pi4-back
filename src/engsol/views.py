
import jwt
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from account.models import Credential
from .models import Project, Client, Condition, Ranking, Note

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
        
        # Decodificar o token usando a chave secreta
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

        # Pega o id do usuário do token
        user_id = decoded.get('user_id')
        user = Credential.objects.get(id=user_id)
        
        # Retornar o user_id se o token for válido
        return user

    except jwt.ExpiredSignatureError:
        return JsonResponse({'error': 'Token expirado'}, status=401)
    
    except jwt.exceptions.InvalidTokenError:
        return JsonResponse({'error': 'Token inválido'}, status=401)
    
    except Credential.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=401)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Criar novo projeto
@csrf_exempt
def create_project(request):


    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente
      
    # Definir metodo
    if request.method == 'POST':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))

            # Carregar dados das repartições do json
            project_data = data['project']
            client_data = data['client']
            timeline = data['timeline']


            # Inserir dados do projeto
            project = Project.objects.create(
                name=project_data['name'],
                key=get_random_string(length=20)
            )

            # Inserir dados do cliente
            client = Client.objects.create(
                project=project,
                name=client_data['name'],
                email=client_data['email']
            )


            # Criar status e rankings na timeline
            for timeline_item in timeline:

                # Obter dados por itens
                ranking_data = timeline_item['ranking']
                condition_data = ranking_data['condition']

                # Carregar dados do status
                condition_id = condition_data.get('id', 0)
                ranking_id = ranking_data.get('id', 0)

                # Verificar se a condição já existe ou precisa ser criada
                if condition_id == 0:
                    
                    # Criar novo condition
                    condition = Condition.objects.create(
                        name=condition_data['name']
                    )

                else:


                    # Obter a condição
                    condition = Condition.objects.get(pk=condition_id)

                # Verificar se o ranking já existe ou precisa ser criado
                if ranking_id == 0:

                    # Criar novo ranking
                    ranking = Ranking.objects.create(
                        project=project,
                        condition=condition,
                        rank=ranking_data['rank'],
                        last_update=ranking_data.get('last_update', None),
                        note=ranking_data['note'],
                        description=ranking_data.get('description', None)
                    )

            # Resposta de sucesso
            response_data = {
                'message': 'Projeto criado com sucesso'
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


# Atualizar projeto
@csrf_exempt
def update_project(request):


    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Definir metodo
    if request.method == 'PUT':

        try:

            # Carregar dados do json
            data = json.loads(request.body.decode('utf-8'))


            # Carregar dados das repartições do json
            project_data = data['project']
            client_data = data['client']
            timeline = data['timeline']

            # Atualizar projeto
            project = get_object_or_404(Project, id=project_data['id'])
            project.name = project_data['name']
            project.save()

            # Atualizar cliente

            client = get_object_or_404(Client, project=project)
            client.name = client_data['name']
            client.email = client_data['email']
            client.save()

            # Atualizar ou criar status e rankings na timeline
            for timeline_item in timeline:

                # Obter dados por itens
                ranking_data = timeline_item['ranking']

                condition_data = ranking_data['condition']

                # Carregar dados do status
                condition_id = condition_data.get('id', 0)
                ranking_id = ranking_data.get('id', 0)
                ranking_delete = ranking_data.get('delete', False)

                # Verificar se a condição já existe ou precisa ser criada
                if condition_id == 0:
                
                    # Criar novo condition
                    condition = Condition.objects.create(
                        name=condition_data['name']
                    )

                else:

                    # Obter a condição
                    condition = Condition.objects.get(pk=condition_id)

                # Verificar se o ranking já existe ou precisa ser criado
                if ranking_id == 0:

                    # Criar novo ranking
                    ranking = Ranking.objects.create(
                        project=project,
                        condition=condition,
                        rank=ranking_data['rank'],

                        last_update=ranking_data.get('last_update', None),
                        note=ranking_data['note'],
                        description=ranking_data.get('description', None)
                    )                   

                else:

                    # Verificar condição para deletar
                    if ranking_delete:

                        # Deletar ranking
                        ranking = get_object_or_404(Ranking, id=ranking_id)
                        ranking.delete()

                    else:

                        # Atualizar ranking existente
                        ranking = get_object_or_404(Ranking, id=ranking_id)
                        ranking.condition = condition
                        ranking.rank = ranking_data['rank']
                        ranking.last_update = ranking_data['last_update']
                        ranking.note = ranking_data['note']
                        ranking.description = ranking_data.get('description', None)
                        ranking.save()

            response_data = {'message': 'Projeto atualizado com sucesso'}
            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


# Deletar projeto
@csrf_exempt
def delete_project(request):

    # Valida o token e retorna o usuário autenticado ou erro JSON
    user = validate_token(request)

    if isinstance(user, JsonResponse):
        return user  # Retorna o erro de autenticação diretamente

    # Definir metodo
    if request.method == 'DELETE':

        try:

            # Buscar parametros na url
            id = request.GET.get('id', None)

            # Buscar o projeto pelo ID
            project = get_object_or_404(Project, id=id)

            # Deletar o projeto
            project.delete()

            # Resposta de sucesso
            response_data = {
                'message': 'Projeto, cliente e ranking deletado com sucesso'
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:

            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

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
