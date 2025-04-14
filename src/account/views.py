from django.shortcuts import render

# Create your views here.
# Importar as models (tabelas)
from .models import Credential
# Importar forms para salvar no banco
from .forms import CredentialForm
# Importar configurações para Json e HTTP
from django.http import JsonResponse
import json
# Evitar problemas CSFR
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
# Criar token
import jwt
import time
from django.conf import settings

# Login
@csrf_exempt
def login(request):
    # Verifica se o método da requisição é POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carrega o corpo da requisição como JSON
        data = json.loads(request.body)

        # Obtém os dados enviados
        email = data.get('email')
        password = data.get('password')

        # Verifica se os campos obrigatórios foram preenchidos
        if not email or not password:
            errors = {
                'email': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not email else [],
                'password': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not password else [],
            }
            return JsonResponse({'errors': errors}, status=400)

        # Tenta encontrar o usuário pelo email
        try:
            user = Credential.objects.get(email=email)

            # Verifica se a senha está correta
            if not password == user.password:
                return JsonResponse({'error': 'Credenciais inválidas'}, status=400)

            # Gera token caso ainda não exista (usuários antigos)
            if not user.token:
                user.token = user.generate_token()
                user.save()

            # Define a duração do token (1 dia, por exemplo)
            expiry_timestamp = int(time.time()) + 86400

            # Monta o payload de resposta
            payload = {
                'token': user.token,
                'expiry_timestamp': expiry_timestamp,
                'user_id': user.id,
                'user_email': user.email,
                'user_name': user.name,
            }

            # Retorna resposta de sucesso com os dados
            return JsonResponse({'message': 'Login realizado com sucesso', 'payload': payload})

        except Credential.DoesNotExist:
            return JsonResponse({'error': 'Usuário não encontrado'}, status=400)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    
# Cadastro
@csrf_exempt
def signup(request):
    # Verifica se a requisição é do tipo POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carrega o corpo da requisição como JSON
        data = json.loads(request.body)

        # Obtém os dados enviados
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        # Verifica se os campos obrigatórios foram preenchidos
        if not all([name, email, password]):
            errors = {
                'name': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not name else [],
                'email': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not email else [],
                'password': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not password else [],
            }
            return JsonResponse({'errors': errors}, status=400)

        # Verifica se já existe uma conta com o e-mail informado
        if Credential.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Já existe uma conta cadastrada com este e-mail'}, status=400)

        # Cria o usuário com senha criptografada
        user = Credential.objects.create(
            name=name,
            email=email,
            password=password,
            status=True,
            auth_code=get_random_string(length=6),
            token='',
        )

        # Gera e salva o token fixo
        user.token = user.generate_token()
        user.save()

        # Retorna mensagem de sucesso
        return JsonResponse({'message': 'Cadastro realizado com sucesso'})

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def admin_create(request):
    # Verifica se a requisição é do tipo POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Carrega o corpo da requisição como JSON
        data = json.loads(request.body.decode('utf-8'))

        # Obtém os dados enviados
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        auth_code = data.get('auth_code')

        if not all([email, password, name, auth_code]):
            return JsonResponse({'error': 'Campos obrigatórios: name, email, password, auth_code'}, status=400)

        # Verifica se o auth_code existe em algum registro
        if not Credential.objects.filter(auth_code=auth_code).exists():
            return JsonResponse({'error': 'Código de autorização inválido'}, status=403)

        # Verifica se o e-mail já está cadastrado
        if Credential.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Usuário já existe'}, status=409)

        # Cria o novo usuário
        user = Credential.objects.create(
            name=name,
            email=email,
            password=password,
            status=True,
            auth_code=get_random_string(length=6),
            token='',
        )

        # Gera e salva o token fixo
        user.token = user.generate_token()
        user.save()

        # Retorna mensagem de sucesso
        return JsonResponse({
            'message': 'Usuário criado com sucesso',
            'email': user.email,
            'name': user.name,
        }, status=201)

    except Exception as e:
        # Retorna erro genérico em caso de exceções
        return JsonResponse({'error': str(e)}, status=500)
    