from django.db import models

# Create your models here.
class transportadoraModels(models.Model):
    transportadora = models.CharField(max_length=50, null=True, blank=True)