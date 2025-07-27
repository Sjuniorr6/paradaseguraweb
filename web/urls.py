from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from mapa.views import get_t42_data,get_devices_data
from pparada.views import ParadaseguraListAPIView
from mapa.views import TrafegusVeiculoView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('login.urls')),
    path('home/', include('home.urls')),
    path('pparada/', include('pparada.urls')),
    path('service/', include('service.urls')),
    path('empresas/', include('empresas.urls')),
    path('transportadora/', include('transportadora.urls')),
    path('mapa/', include('mapa.urls')),  # <-- Adicione a vírgula no final desta linha
    path('api/get_t42_data/', get_t42_data, name='get_t42_data'),
    path('api/paradasegura/', ParadaseguraListAPIView.as_view(), name='paradasegura-list'),
    path('trafegus/veiculo/', TrafegusVeiculoView.as_view(), name='trafegus_veiculo'),
    path('get_devices_data/', get_devices_data, name='get_devices_data'),
]

# Adicionar URLs para servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
