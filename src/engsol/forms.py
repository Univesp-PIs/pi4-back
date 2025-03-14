from django import forms
from .models import Project, Client, Ranking

# Formulário para o modelo Project
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date']  # Ajuste os campos conforme o seu modelo

# Formulário para o modelo Client
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone_number']  # Ajuste os campos conforme o seu modelo

# Formulário para o modelo Ranking
class RankingForm(forms.ModelForm):
    class Meta:
        model = Ranking
        fields = ['name', 'rank', 'project', 'status']  # Ajuste os campos conforme o seu modelo
