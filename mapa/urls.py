from django.urls import path
from .views import get_t42_data,MapaView,get_devices_data,TrafegusVeiculoView

urlpatterns = [
   
    path('api/get_t42_data/', get_t42_data, name="get_t42_data"),
    path("mapa/", MapaView.as_view(), name="mapa"),
    
    path('get_devices_data/', get_devices_data, name='get_devices_data'),
    path('trafegus/veiculo/', TrafegusVeiculoView.as_view(), name='trafegus_veiculo'),
    
    
]
