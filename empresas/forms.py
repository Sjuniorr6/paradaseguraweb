from django import forms
from .models import empresasModels

class EmpresasForm(forms.ModelForm):
    class Meta:
        model = empresasModels
        fields = [
            'tipoempresa',
            'tipopessoa',
            'razaosocial',
            'nomefantasia',
            'cnpj',
        ]
