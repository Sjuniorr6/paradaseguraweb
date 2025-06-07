# Create your models here.
from django.db import models
from django.conf import settings

class AlertLog(models.Model):
    ALERT_TYPES = [
        ('button', 'Botão'),
        ('geofence', 'Cerca Geográfica'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='button')
    button = models.CharField(max_length=50, null=True, blank=True)
    geofence_name = models.CharField(max_length=100, null=True, blank=True)
    vehicle_plate = models.CharField(max_length=20, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        if self.alert_type == 'button':
            return f"{self.user} clicou em {self.button} em {self.timestamp:%Y-%m-%d %H:%M:%S}"
        else:
            return f"Veículo {self.vehicle_plate} entrou na cerca {self.geofence_name} em {self.timestamp:%Y-%m-%d %H:%M:%S}"