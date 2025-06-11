from django.urls import path
from .views import get_t42_data, MapaView2, get_devices_data, ultima_posicao_veiculos, trafegus_veiculos
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('api/get_t42_data/', get_t42_data, name="get_t42_data"),
    path("mapa2/", MapaView2.as_view(), name="mapa2"),
    path('ultima-posicoes/', ultima_posicao_veiculos, name='ultima-posicoes'),
    path('get_devices_data/', get_devices_data, name='get_devices_data'),
    path('trafegus_veiculos/', trafegus_veiculos, name="trafegus_veiculos"),
    path('service/trafegus_veiculos/', trafegus_veiculos, name="trafegus_veiculos"),
    path('remove-alert/', views.remove_alert, name='remove_alert'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))