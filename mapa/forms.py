from django import forms
from .models import Equipamento

class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = "__all__"

        widgets = {
            # Campos de data (DateField ou DateTimeField)
            'data_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_insercao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_chegada_destino': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_retirada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_envio_brasil': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_brasil': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_desembarque_maritimo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_do_desembarque': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),

            # Se 'data_embarque_maritimo' for DateField, use DateInput. 
            # Mas se for CharField (como no seu model), use TextInput:
            'data_embarque_maritimo': forms.TextInput(attrs={'class': 'form-control'}),

            # Campos de texto (CharField)
            'requisicao': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'local_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'identificador': forms.TextInput(attrs={'class': 'form-control'}),
            'CCID': forms.TextInput(attrs={'class': 'form-control'}),
            'BL': forms.TextInput(attrs={'class': 'form-control'}),
            'container': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'local_atual': forms.TextInput(attrs={'class': 'form-control'}),
            'status_do_container': forms.TextInput(attrs={'class': 'form-control'}),

            # Campos de número (IntegerField, FloatField, etc.)
            'sla_insercao': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_viagem': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_retirada': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_envio_brasil': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_operacao': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_terrestre': forms.NumberInput(attrs={'class': 'form-control'}),
            'sla_maritimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),

            # Campos de escolha (CharField com choices ou similar)
            'status_operacao': forms.Select(attrs={'class': 'form-control'}),

            # Campos de texto longo (TextField)
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),

            # Se 'reposicao' for CharField mas você quiser checkbox, 
            # lembre que vai salvar "on" ou "off". 
            # Se for BooleanField no model, isso está correto.
            'reposicao': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
