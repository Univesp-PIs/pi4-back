from django.db import models
import jwt
from django.conf import settings

# Create your models here.
class Credential(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    token = models.TextField(blank=True, null=True)
    auth_code = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'account'

    def __str__(self):
        return self.email

    def generate_token(self):
        payload = {'user_id': self.id}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
class EmailConfiguration(models.Model):
    email = models.CharField(max_length=100)  # Endereço de e-mail usado para o envio
    password = models.CharField(max_length=100)  # Senha do e-mail ou app password
    smtp_server = models.CharField(max_length=100)  # Servidor SMTP (ex: smtp.gmail.com)
    smtp_port = models.IntegerField()  # Porta SMTP (ex: 587 ou 465)
    use_ssl = models.BooleanField(default=False)  # Indica se deve usar SSL/TLS
    status = models.BooleanField(default=True)  # Ativo ou inativo
    created_at = models.DateTimeField(auto_now_add=True)  # Data de criação
    updated_at = models.DateTimeField(auto_now=True)  # Data de atualização

    def __str__(self):
        return f"{self.email} ({self.smtp_server}:{self.smtp_port})"