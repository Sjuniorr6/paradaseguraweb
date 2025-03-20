from django.shortcuts import render
from django.urls import reverse_lazy
from .models import paradasegura, passagemmodel
from .forms import paradaForm,PassagemModelForm
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from .models import paradasegura
from time import time
from django.shortcuts import redirect
from .models import paradasegura
from .forms import paradaForm
 # Importe a função criada
from .forms import paradaForm
from PIL import Image, ImageDraw, ImageFont
import os
import time
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class paradaCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = paradasegura
    template_name = 'parada_create.html'
    form_class = paradaForm
    success_url = reverse_lazy('paradaseguraform')
    permission_required = "pparada.add_paradasegura"

    def form_valid(self, form):
        # Salva o objeto primeiro
        response = super().form_valid(form)

        # Lista dos campos de imagem a serem verificados para aplicar a marca d'água
        campos_imagem = ['foto_cavalo', 'foto_documento_cavalo', 'foto_carreta', 'foto_carreta_documento', 'cnh']

        # Itera sobre os campos de imagem e aplica a marca d'água se a imagem existir
        for campo in campos_imagem:
            imagem = getattr(self.object, campo, None)
            if imagem and hasattr(imagem, 'path') and os.path.exists(imagem.path):
                print(f"Aplicando marca d'água na imagem: {imagem.path}")
                add_watermark(imagem.path)

        return response

def add_watermark(image_path, watermark_text="Grupo Golden Sat / Parada Segura"):
    try:
        # Verifica se a imagem existe
        if not os.path.exists(image_path):
            print(f"Imagem não encontrada: {image_path}")
            return

        # Abre a imagem original e converte para RGBA (necessário para adicionar a camada de marca d'água)
        original_image = Image.open(image_path).convert("RGBA")
        print(f"Imagem original carregada com sucesso: {image_path}")

        # Cria uma nova imagem transparente para a camada de marca d'água
        txt_layer = Image.new("RGBA", original_image.size, (255, 255, 255, 0))

        # Configura o objeto de desenho para escrever na camada de marca d'água
        draw = ImageDraw.Draw(txt_layer)

        # Carrega a fonte (use uma fonte adequada que esteja disponível no sistema)
        try:
            font = ImageFont.truetype("arial.ttf", 48)  # Altere para uma fonte válida em seu sistema
        except IOError:
            font = ImageFont.load_default()  # Usa a fonte padrão se a fonte especificada não estiver disponível

        # Calcula o tamanho do texto
        text_width, text_height = draw.textsize(watermark_text, font=font)

        # Posiciona a marca d'água no canto inferior direito
        padding = 20  # Distância das bordas
        text_position = (original_image.width - text_width - padding, original_image.height - text_height - padding)

        # Adiciona o texto da marca d'água à camada de marca d'água
        draw.text(text_position, watermark_text, fill=(255, 255, 255, 255), font=font)  # Cor branca sem transparência
        print(f"Marca d'água adicionada na posição: {text_position}")

        # Combina a imagem original com a camada de marca d'água
        watermarked_image = Image.alpha_composite(original_image, txt_layer)

        # Converte a imagem resultante para RGB antes de salvar no formato JPEG (sem canal alfa)
        watermarked_image = watermarked_image.convert("RGB")

        # Salva a imagem com a marca d'água, substituindo a original
        watermarked_image.save(image_path, format="JPEG")
        print(f"Marca d'água aplicada com sucesso em {image_path}")

    except Exception as e:
        print(f"Erro ao aplicar marca d'água: {e}")



class passagemCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = passagemmodel
    template_name = 'passagem.html'
    form_class = PassagemModelForm
    success_url = reverse_lazy('passagemCreateView')
    permission_required = "pparada.add_paradasegura"
    

    


from django.views.generic import ListView
from .models import passagemmodel

class PassagemListView(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = passagemmodel
    template_name = 'historico_passagem.html'
    context_object_name = 'passagens'
    paginate_by = 10  # Defina quantas entradas por página você desej
    permission_required = "pparada.add_paradasegura"
    def get_queryset(self):
        return passagemmodel.objects.all().order_by('-data_criacao') 


from django.db.models import Q

class historicoListView(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = paradasegura
    template_name = 'historico_paradas.html'
    context_object_name = 'pa'
    paginate_by = 10  # Quantas entradas por página
    permission_required = "pparada.add_paradasegura"
    def get_queryset(self):
        queryset = paradasegura.objects.all().order_by('-data_criacao')
        
        # Filtrar pelo parâmetro 'embarcador' se estiver presente na URL
        embarcador = self.request.GET.get('embarcador')
        if embarcador:
            queryset = queryset.filter(embarcador__icontains=embarcador)

        return queryset
    


from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

class Parada2DetailView(LoginRequiredMixin,DetailView):
    model = paradasegura
    template_name = 'parada_detail2.html'
    context_object_name = 'parada'
   

    


from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView
from .models import paradasegura

class paradaListView(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = paradasegura
    template_name = 'pa_list.html'
    context_object_name = 'pa'
    paginate_by = 12
    permission_required = "pparada.add_paradasegura"

    def get_queryset(self):
        # Obter todos os objetos de paradasegura cujo status seja "Aguardando"
        queryset = paradasegura.objects.filter(status='AGUARDANDO').order_by('-id')

        # Obter o valor do campo 'embarcador' do request GET
        embarcador = self.request.GET.get('embarcador', None)

        # Filtrar pelo campo 'embarcador' se houver valor fornecido
        if embarcador:
            queryset = queryset.filter(Q(embarcador__icontains=embarcador))

        return queryset

class RegistrarSaidaView(LoginRequiredMixin,PermissionRequiredMixin,View):
    permission_required = "pparada.add_paradasegura"

    def get(self, request, pk, *args, **kwargs):
        parada = get_object_or_404(paradasegura, pk=pk)

        # Atualizar o status para 'EM VIAGEM' e definir a data de saída
        parada.status = 'EM VIAGEM'
        parada.saida = timezone.now()
        parada.save()

        # Redirecionar de volta para a lista de paradas
        return redirect('paradaseguralist')
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import paradasegura

class ParadaDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = paradasegura
    template_name = 'parada_detail.html'
    context_object_name = 'parada'
    permission_required = "pparada.add_paradasegura"
    



from django.http import JsonResponse

def get_choices(request):
    tipo_posto = request.GET.get('tipo_posto')
    print(f'Tipo de posto: {tipo_posto}')  # Debugging
    response_data = {
        'iscas': [],
        'cadeados': [],
        'pa': []
    }

    if tipo_posto:
        if tipo_posto in paradasegura.POSTOS_INFO1:
            iscas = paradasegura.POSTOS_INFO1[tipo_posto].get('iscas', [])
            cadeados = paradasegura.POSTOS_INFO1[tipo_posto].get('cadeados', [])
            response_data['iscas'] = iscas
            response_data['cadeados'] = cadeados
            print(f'Iscas: {iscas}, Cadeados: {cadeados}')  # Debugging

        if tipo_posto in paradasegura.POSTOS_INFO2:
            pa = paradasegura.POSTOS_INFO2[tipo_posto].get('pa', [])
            response_data['pa'] = pa
            print(f'PA: {pa}')
    return JsonResponse(response_data)

def get_pa_choices(request):
    tipo_posto = request.GET.get('tipo_posto')
    print(f'Tipo de posto: {tipo_posto}')  # Debugging
    if tipo_posto and tipo_posto in passagemmodel.POSTOS_INFO2:
        pa = passagemmodel.POSTOS_INFO2[tipo_posto]['pa']
        print(f'PA: {pa}')  # Debugging
        return JsonResponse({
            'pa': pa,
        })
    return JsonResponse({'pa': []})



# views.py
from django.views.generic import TemplateView
from .models import paradasegura

class EquipamentosPorPostoView(LoginRequiredMixin,TemplateView):
    template_name = 'equipamentos_por_posto.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # POSTO é uma lista de tuplas (código, nome)
        postos = paradasegura.POSTO
        info_cadeados_iscas = paradasegura.POSTOS_INFO1  # Equipamentos (cadeados e iscas)
        info_pa = paradasegura.POSTOS_INFO2  # PA (nome do PA)
        
        equipamentos = {}
        for code, nome in postos:
            if code == '0':  # pula o valor '---'
                continue
            cadeados = info_cadeados_iscas.get(code, {}).get('cadeados', [])
            iscas = info_cadeados_iscas.get(code, {}).get('iscas', [])
            pa = info_pa.get(code, {}).get('pa', [])
            equipamentos[nome] = {
                'cadeados': cadeados,
                'iscas': iscas,
                'pa': pa,
            }
        context['equipamentos'] = equipamentos
        return context



from rest_framework import generics
from .models import paradasegura
from .serializers import ParadaseguraSerializer

class ParadaseguraListAPIView(generics.ListAPIView):
    queryset = paradasegura.objects.all()
    serializer_class = ParadaseguraSerializer



from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import paradasegura_ponto
from .forms import ParadaseguraPontoForm  # Caso você tenha definido um formulário personalizado

class PontoCreateView(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = paradasegura_ponto
    form_class = ParadaseguraPontoForm  # Se você não usar um formulário customizado, pode usar "fields = ['nome', 'descricao']" aqui.
    template_name = 'ponto_create.html'
    success_url = reverse_lazy('ponto_list')  # Altere conforme a URL desejada após a criação
    permission_required = "pparada.add_paradasegura"



class paradaListView2(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    model = paradasegura
    template_name = 'tabela_acionamentos.html'
    context_object_name = 'pa'
    paginate_by = 10  # Quantas entradas por página
    permission_required = "empresas.add_empresasmodels"
    def get_queryset(self):
        queryset = paradasegura.objects.all().order_by('-data_criacao')
        
        # Filtrar pelo parâmetro 'embarcador' se estiver presente na URL
        embarcador = self.request.GET.get('embarcador')
        if embarcador:
            queryset = queryset.filter(embarcador__icontains=embarcador)

        return queryset
    
    from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import paradasegura

@require_POST
def parada_delete(request, id):
    obj = get_object_or_404(paradasegura, id=id)
    obj.delete()
    return redirect('paradaseguralist2')  # Ajuste para o nome correto da sua rota



# views.py
from django.views.generic import ListView
from django.db.models import Q
from django.utils import timezone
from .models import paradasegura
from django.views.generic import ListView
from django.db.models import Q
from django.http import HttpResponse
import openpyxl

from .models import paradasegura

class ParadaSeguraListView(ListView):
    model = paradasegura
    template_name = 'relatorios.html'       # Nome do template
    context_object_name = 'object_list'     # Nome do contexto usado no template
    paginate_by = 10                        # Valor padrão de paginação

    def get_queryset(self):
        queryset = super().get_queryset()

        # Recupera parâmetros de filtro do GET
        embarcador = self.request.GET.get('embarcador', '')
        data_inicio = self.request.GET.get('data_inicio', '')
        data_fim = self.request.GET.get('data_fim', '')
        search = self.request.GET.get('search', '')

        # Filtra por embarcador (igualdade exata, como no seu código)
        if embarcador:
            queryset = queryset.filter(embarcador=embarcador)

        # Filtra por data (YYYY-MM-DD) em data_criacao
        if data_inicio:
            queryset = queryset.filter(data_criacao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_criacao__date__lte=data_fim)

        # Filtro de busca (placa, motorista, etc.)
        if search:
            queryset = queryset.filter(
                Q(placa_cavalo__icontains=search) |
                Q(placa_carreta__icontains=search) |
                Q(nome_motorista__icontains=search) |
                Q(id_cadeado__icontains=search)
            )

        return queryset

    def get_paginate_by(self, queryset):
        """Permite escolher quantos registros exibir por página (via GET)."""
        return self.request.GET.get('mostrar_registros', self.paginate_by)


def export_excel(request):
    """Exporta em Excel os mesmos filtros aplicados na listagem."""
    # 1. Obter parâmetros de pesquisa
    embarcador = request.GET.get('embarcador', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    search = request.GET.get('search', '')

    # 2. Aplicar a mesma lógica de filtros do ParadaSeguraListView
    queryset = paradasegura.objects.all()

    if embarcador:
        queryset = queryset.filter(embarcador=embarcador)

    if data_inicio:
        queryset = queryset.filter(data_criacao__date__gte=data_inicio)
    if data_fim:
        queryset = queryset.filter(data_criacao__date__lte=data_fim)

    if search:
        queryset = queryset.filter(
            Q(placa_cavalo__icontains=search) |
            Q(placa_carreta__icontains=search) |
            Q(nome_motorista__icontains=search) |
            Q(id_cadeado__icontains=search)
        )

    # 3. Criar a planilha Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Checklist'

    # 4. Cabeçalhos
    headers = [
        'Embarcador', 'Motorista', 'Placa Cavalo', 'Placa Carreta',
        'Data Criação', 'Tipo Parada', 'ID Cadeado', 'Status', 'Saída'
    ]
    ws.append(headers)

    # 5. Inserir dados
    for item in queryset:
        ws.append([
            item.embarcador,
            item.nome_motorista,
            item.placa_cavalo,
            item.placa_carreta,
            item.data_criacao.strftime('%d/%m/%Y %H:%M') if item.data_criacao else '',
            item.tipo_parada,
            item.id_cadeado,
            item.status,
            item.saida.strftime('%d/%m/%Y %H:%M') if item.saida else ''
        ])

    # 6. Montar a resposta para download
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="checklist.xlsx"'

    # 7. Salvar a planilha no response
    wb.save(response)
    return response
