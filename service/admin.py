from django.contrib import admin
from .models import Geofence, UserGeofence
from django.http import JsonResponse

# Register your models here.

admin.site.register(Geofence)
admin.site.register(UserGeofence)

def get_devices_data(request):
    user = request.user
    # Busca as cercas vinculadas ao usuário
    geofences = [
        {
            "name": g.geofence.nome,
            "center": [g.geofence.latitude, g.geofence.longitude],
            "radius": g.geofence.raio
        }
        for g in UserGeofence.objects.filter(user=user)
    ]
    # ...retorne geofences no JSON...
    return JsonResponse({"geofences": geofences})
