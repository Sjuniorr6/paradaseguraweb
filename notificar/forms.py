from django import forms
from .models import AlertLog

class AlertLogForm(forms.ModelForm):
    class Meta:
        model = AlertLog
        fields = ['button']
        widgets = {
            'button': forms.HiddenInput(),
        }