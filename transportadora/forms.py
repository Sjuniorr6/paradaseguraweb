# forms.py
from django import forms
from .models import transportadoraModels

class TransportadoraForm(forms.ModelForm):
    class Meta:
        model = transportadoraModels
        fields = ["transportadora"]
        labels = {
            "transportadora": "Nome da Transportadora",
        }
