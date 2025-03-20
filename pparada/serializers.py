from rest_framework import serializers
from .models import paradasegura

class ParadaseguraSerializer(serializers.ModelSerializer):
    class Meta:
        model = paradasegura
        fields = '__all__'
