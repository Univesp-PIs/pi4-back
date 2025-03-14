from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import *
from . import views

class LoginTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.url = reverse('login')
        cls.user = Credential.objects.create(
            name="user123", 
            email="janedoe@test.com", 
            password="password456")
    
    def test_login_with_success(self):
        data = {
            "email": "janedoe@test.com",
            "password": "password456"
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        response_content = response.content.decode('utf-8')
        response_data = json.loads(response_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['message'], 'Login realizado com sucesso')
    
    def test_invalid_credentials(self):
        data = {
            "email": "janedoe@test.com",
            "password": "bla"
        }
        
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        response_content = response.content.decode('utf-8')
        response_data = json.loads(response_content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['error'], 'Credenciais inválidas')

    def test_user_not_found(self):
        data = {
            "email": "test@test.com",
            "password": "password456"
        }
        
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        response_content = response.content.decode('utf-8')
        response_data = json.loads(response_content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['error'], 'Usuário não encontrado')
    
    def test_password_and_email_required(self):        
        data = {}
        response = self.client.post(self.url, data=json.dumps(data), content_type='application/json')
        response_content = response.content.decode('utf-8')
        response_data = json.loads(response_content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_data['errors']['email'][0]['message'], 'Este campo é obrigatório.')
        self.assertEqual(response_data['errors']['password'][0]['message'], 'Este campo é obrigatório.')