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
# Criar token
import jwt
import time
from django.conf import settings

# Login
@csrf_exempt
def login(request):

    # Verificamos se o método da solicitação é POST
    if request.method == 'POST':

        # Obter o corpo da solicitação e carregar os dados JSON
        data = json.loads(request.body)

        # Verificar se os campos de email e senha estão presentes
        email = data.get('email')
        password = data.get('password')

        if email and password:

            try:

                # Buscar o usuário no banco de dados pelo email
                user = Credential.objects.get(email=email)

                if password == user.password:

                    # Usar token fixo salvo no banco
                    token = user.token

                    # Caso o token ainda não tenha sido gerado (para usuários antigos)
                    if not token:
                        token = user.generate_token()
                        user.token = token
                        user.save()

                    # Definir a duração do token (por exemplo, 1 dia)
                    token_lifetime_seconds = 86400  # 1 dia
                    expiry_timestamp = int(time.time()) + token_lifetime_seconds

                    # Gerar resposta json payload
                    payload = {'token':token, 'expiry_timestamp': expiry_timestamp, 'user_id': user.id, 'user_email': email, 'user_name': user.name}

                    # Retornar uma mensagem de sucesso
                    #return JsonResponse({'message': 'Login realizado com sucesso', 'token': token, 'id': user.id})
                    return JsonResponse({'message': 'Login realizado com sucesso', 'payload': payload})
                
                else:

                    # Senha incorreta, retornar mensagem de erro
                    return JsonResponse({'error': 'Credenciais inválidas'}, status=400)
                
            except Credential.DoesNotExist:

                # Usuário não encontrado, retornar mensagem de erro
                return JsonResponse({'error': 'Usuário não encontrado'}, status=400)
            
        else:
            
            errors = {
                'email': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not email else [],
                'password': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not password else [],
            }

            return JsonResponse({'errors': errors}, status=400)
        
    else:

        # Método não permitido, retornar mensagem de erro
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
# Cadastro
@csrf_exempt
def signup(request):

    # Verificamos se o método da solicitação é POST
    if request.method == 'POST':

        # Obter o corpo da solicitação e carregar os dados JSON
        data = json.loads(request.body)

        # Verificar se os campos de email e senha estão presentes
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        # Se ambos os campos estiverem presentes, continue com o processamento
        if name and email and password:

            # Verificar se já existe uma credencial com o mesmo e-mail no banco de dados
            existing_credential = Credential.objects.filter(email=email).first()

            if not existing_credential:

                # Criar um formulário com os dados recebidos
                form = CredentialForm(data)

                if form.is_valid():

                    # Salvar os dados no banco de dados
                    new_user = form.save()

                    # Gerar token fixo e salvar no usuário
                    new_user.token = new_user.generate_token()
                    new_user.save()
                
                    # Sua lógica de criação de usuário aqui
                    return JsonResponse({'message': 'Cadastro realizado com sucesso'})
                
                else:

                    # Retornar uma resposta JSON com erros de validação
                    return JsonResponse({'errors': form.errors}, status=400)
                
            else:
                # Se já existir uma credencial com este e-mail, retorne uma mensagem de erro
                return JsonResponse({'error': 'Já existe uma conta cadastrada com este e-mail'}, status=400)
        
        else:

            errors = {
                'name': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not name else [],
                'email': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not email else [],
                'password': [{'message': 'Este campo é obrigatório.', 'code': 'required'}] if not password else [],
            }

            return JsonResponse({'errors': errors}, status=400)
        
    else:

        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
