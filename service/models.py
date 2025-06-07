from django.db import models
from django.contrib.auth.models import User

class Geofence(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    raio = models.FloatField()  # em metros

    def __str__(self):
        return self.nome

class UserGeofence(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'geofence')

    def __str__(self):
        return f"{self.user.username} - {self.geofence.nome}"
