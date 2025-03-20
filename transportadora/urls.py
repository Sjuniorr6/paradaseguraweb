# urls.py
from django.urls import path
from .views import transportadoraCreate,transportadoraList, transportadora_delete

urlpatterns = [
    
    path('transportadoras/',transportadoraCreate.as_view(),name='criar_transportador'),
    path('transportadoras_list/',transportadoraList.as_view(),name = 'lista_trasportadores'),
    path('transportadoras/delete/<int:pk>/', transportadora_delete,name='transportadora_delete')
    
]