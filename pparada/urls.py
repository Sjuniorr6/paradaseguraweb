from django.urls import path
from.import views
from .views import (
    
    paradaCreateView, 
    paradaListView, 
    get_choices, 
    passagemCreateView,
    PassagemListView, 
    get_pa_choices, 
    ParadaDetailView,
    RegistrarSaidaView,
    historicoListView,
    Parada2DetailView,
    EquipamentosPorPostoView,
    ParadaseguraListAPIView,
    PontoCreateView,
    paradaListView2,
    parada_delete,
    ParadaSeguraListView,
    export_excel,
    paradasegura_api_list,
    paradasegura_api_detail,
    paradasegura_api_create,
    paradasegura_api_update,
    paradasegura_api_delete,
 
 
)

urlpatterns = [
    path('pparada/', paradaCreateView.as_view(), name='paradaseguraform'),
    path('pa_list/', paradaListView.as_view(), name='paradaseguralist'),
    path('pa_list2/', paradaListView2.as_view(), name='paradaseguralist2'),
    path('estoque/', EquipamentosPorPostoView.as_view(), name='estoque'),
    path('get-choices/', get_choices, name='get_choices'),
    path('passagem/', passagemCreateView.as_view(), name='passagemCreateView'),
    path('historico/', PassagemListView.as_view(), name='historico_passagem'),
    path('historico_parada/', historicoListView.as_view(), name='historico_parada'),
    path('get_pa_choices/', get_pa_choices, name='get_pa_choices'),
    path('parada/<int:pk>/detail/', ParadaDetailView.as_view(), name='ParadaDetailView'),
    path('parada2/<int:pk>/detail/', Parada2DetailView.as_view(), name='Parada2DetailView'),
    path('parada/<int:pk>/registrar-saida/', RegistrarSaidaView.as_view(), name='registrar_saida'),
    path('api/paradasegura/', ParadaseguraListAPIView.as_view(), name='paradasegura-list'),
    path('ponto/create/', PontoCreateView.as_view(), name='ponto_create'),
    path('parada/<int:id>/delete/', parada_delete, name='parada_delete'),
    path('relatorios/', ParadaSeguraListView.as_view(), name='parada_segura_list'),
    path('export/excel/', views.export_excel, name='excel_export'),
    
    # API Endpoints JSON
    path('api/json/list/', paradasegura_api_list, name='paradasegura_api_list'),
    path('api/json/<int:pk>/', paradasegura_api_detail, name='paradasegura_api_detail'),
    path('api/json/create/', paradasegura_api_create, name='paradasegura_api_create'),
    path('api/json/<int:pk>/update/', paradasegura_api_update, name='paradasegura_api_update'),
    path('api/json/<int:pk>/delete/', paradasegura_api_delete, name='paradasegura_api_delete'),
]

# Inclua esta parte apenas se estiver em ambiente de desenvolvimento com DEBUG=True
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
