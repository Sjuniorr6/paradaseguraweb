from django.urls import path
from .views import EmpresaCreateView,empresaslist,empresa_delete

urlpatterns = [
    path('empresa/novo/',EmpresaCreateView.as_view(), name='criar_empresa'),
    path('empresa/lista/',empresaslist.as_view(), name='listar_empresa'),
    path('empresas/<int:pk>/delete/', empresa_delete, name='empresa_delete'),
    
    
]