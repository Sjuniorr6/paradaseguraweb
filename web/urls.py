from django.contrib import admin
from django.urls import path, include
from mapa.views import get_t42_data, get_devices_data, TrafegusVeiculoView, STCVeiculosAPIView
from pparada.views import ParadaseguraListAPIView
from django.conf import settings
from django.conf.urls.static import static
import os
from pathlib import Path
from django.shortcuts import redirect

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    str(BASE_DIR / 'static'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login/', permanent=False)),
    path('login/', include('login.urls')),
    path('home/', include('home.urls')),
    path('pparada/', include('pparada.urls')),
    path('service/', include('service.urls')),
    path('empresas/', include('empresas.urls')),
    
    path('notificar/', include('notificar.urls')),
    path('transportadora/', include('transportadora.urls')),
    path('mapa/', include('mapa.urls')),  # <-- Adicione a vírgula no final desta linha
    path('api/get_t42_data/', get_t42_data, name='get_t42_data'),
    path('api/paradasegura/', ParadaseguraListAPIView.as_view(), name='paradasegura-list'),
    path('trafegus/veiculo/', TrafegusVeiculoView.as_view(), name='trafegus_veiculo'),
    path('get_devices_data/', get_devices_data, name='get_devices_data'),
    path('api/stc/veiculos/', STCVeiculosAPIView.as_view(), name='stc_veiculos_api'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)