# login/urls.py
from django.urls import path
from .views import CustomLoginView, CustomLogoutView,RegisterView

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),     # Rota '/' (raiz) -> tela de login
    path('logout/', CustomLogoutView.as_view(), name='logout'),  # Rota '/logout/'
    path('register/', RegisterView.as_view(), name='register'),
]
