# login/views.py
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        # Se o usuário já estiver autenticado, manda para 'home'
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    next_page = 'login'  # ✅ Redireciona para a página de login

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)  # Permite logout via GET




# views.py
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

class RegisterView(CreateView):
    template_name = 'register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

# admin.py

# views.py
