from django.shortcuts import render
from .models import transportadoraModels
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from .forms import TransportadoraForm
from django.urls import reverse_lazy
    
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .models import transportadoraModels
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
# Create your views here.
class transportadoraCreate(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = transportadoraModels
    form_class = TransportadoraForm  
    template_name = 'transportadora.html'
    success_url = reverse_lazy('lista_trasportadores')
    permission_required = "empresas.add_empresasmodels"
    

class transportadoraList(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = transportadoraModels
    template_name = 'transportadora_list.html'
    context_object_name = 'transportadora'
    permission_required = 'empresas.add_empresasmodels'
    
# views.py
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import transportadoraModels

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import transportadoraModels  # ou o nome que estiver usando

@require_POST
def transportadora_delete(request, pk):
    obj = get_object_or_404(transportadoraModels, pk=pk)
    obj.delete()
    return redirect('lista_trasportadores')  # bate com o name='lista_trasportadores'
