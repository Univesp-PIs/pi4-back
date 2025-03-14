from django import forms
from .models import Credential

# Create your forms here
class CredentialForm(forms.ModelForm):
    
    password = forms.CharField(label='Senha', widget=forms.PasswordInput())

    class Meta:
        model = Credential  # Indica qual modelo será utilizado no formulário
        fields = ['name', 'email', 'password']  # Define quais campos do modelo serão utilizados no formulário

# O campo 'password' é definido separadamente para que possamos renderizá-lo como um campo de senha
# Isso significa que a senha digitada pelo usuário será mascarada quando ele a digitar

class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)
    password = forms.CharField(label='Senha', widget=forms.PasswordInput())

# Este é um formulário de login separado que não está associado a nenhum modelo específico
# Ele possui campos para o email e a senha do usuário

# Ambos os formulários podem ser usados nas views para processar os dados fornecidos pelos usuários

