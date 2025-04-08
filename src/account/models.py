from django.db import models
import jwt
from django.conf import settings

# Create your models here.
class Credential(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    token = models.TextField(blank=True, null=True)
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