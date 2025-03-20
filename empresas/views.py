from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import empresasModels
from .forms import EmpresasForm
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import empresasModels
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class EmpresaCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = empresasModels
    form_class =EmpresasForm 
    template_name ='empresa_form.html'
    success_url= reverse_lazy('listar_empresa')
    permission_required = "empresas.add_empresasmodels"
        
class empresaslist(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = empresasModels
    template_name ='lista_empresas.html'
    context_object_name = 'empresa'
    permission_required = "empresas.add_empresasmodels"
    
    # views.py

@require_POST
def empresa_delete(request, pk):
    obj = get_object_or_404(empresasModels, pk=pk)
    obj.delete()
    return redirect('listar_empresa')  # Ajuste para o name correto da sua listagem
