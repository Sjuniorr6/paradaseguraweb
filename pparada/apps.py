# pparada/apps.py
from django.apps import AppConfig

class PparadaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pparada'

    def ready(self):
        import pparada.signals  # Carrega os sinais corretamente
