from django.shortcuts import render

from django.views.generic import TemplateView,CreateView
import requests
from django.shortcuts import render
from django.http import JsonResponse


# Create your views here.
T42_API_URL = "https://mongol.brono.com/mongol/api.php"
T42_USER = "gs_paradasegura"
T42_PASS = "GGS@20xx"
def get_t42_data(request):
    params = {
        "commandname": "get_last_transmits",
        "user": T42_USER,
        "pass": T42_PASS,
        "format": "json"
    }
    
    try:
        response = requests.get(T42_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        # Retorne o JSON sem filtro para verificar sua estrutura
        return JsonResponse(data, safe=False)
    
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


import time
import requests
from django.http import JsonResponse

# Configuração das APIs
T42_API_URL = "https://mongol.brono.com/mongol/api.php"
T42_USER = "gs_paradasegura"
T42_PASS = "GGS@20xx"

STC_API_URL = "http://ap3.stc.srv.br/integration/prod/ws/getClientVehicles"
STC_KEY = "d548f2c076480dcc2bd69fcbf8e6be61"
STC_USER = "quality.paradasegura"
STC_PASS = "6b25cff77f9bad60a73fa81daa7d06ae"

# 🔥 Variáveis globais para armazenar os últimos dados válidos
ultima_chamada_t42 = 0
ultima_resposta_t42 = []
ultima_chamada_stc = 0
ultima_resposta_stc = None  # Agora começa como None para evitar sobrescritas erradas

def get_devices_data(request):
    """Obtém os dados das APIs T42 e STC e retorna um JSON combinado, garantindo que dados antigos sejam usados se necessário."""
    global ultima_chamada_t42, ultima_resposta_t42
    global ultima_chamada_stc, ultima_resposta_stc

    tempo_atual = time.time()

    # 🔵 API T42 (Se passou mais de 60s desde a última chamada)
    if tempo_atual - ultima_chamada_t42 >= 60:
        params_t42 = {
            "commandname": "get_last_transmits",
            "user": T42_USER,
            "pass": T42_PASS,
            "format": "json"
        }
        try:
            t42_response = requests.get(T42_API_URL, params=params_t42, verify=False)
            if t42_response.status_code == 200:
                t42_data = t42_response.json()
                if t42_data:  # Se houver dados, armazena
                    ultima_resposta_t42 = t42_data
                    ultima_chamada_t42 = tempo_atual
                else:
                    print("⚠️ API T42 retornou um JSON sem dados. Mantendo os últimos dados registrados.")
            else:
                print(f"⚠️ API T42 falhou com status {t42_response.status_code}. Mantendo os últimos dados.")
        except requests.RequestException as e:
            print(f"⚠️ Erro ao chamar a API T42: {e}. Mantendo os últimos dados.")
    else:
        print("⏳ API T42 chamada recentemente. Retornando últimos dados armazenados.")

    # 🔴 API STC (Se passou mais de 60s desde a última chamada)
    if tempo_atual - ultima_chamada_stc >= 60:
        payload_stc = {
            "key": STC_KEY,
            "user": STC_USER,
            "pass": STC_PASS
        }
        try:
            stc_response = requests.post(STC_API_URL, json=payload_stc, verify=False)
            if stc_response.status_code == 200:
                stc_raw_data = stc_response.json()
                if "data" in stc_raw_data and stc_raw_data["data"]:
                    ultima_resposta_stc = stc_raw_data["data"]  # ✅ Apenas sobrescreve se houver dados
                    ultima_chamada_stc = tempo_atual
                    print("✅ API STC atualizada com novos dados.")
                else:
                    print("⚠️ API STC retornou um JSON vazio. Mantendo últimos dados válidos.")
            else:
                print(f"⚠️ API STC falhou com status {stc_response.status_code}. Mantendo os últimos dados.")
        except requests.RequestException as e:
            print(f"⚠️ Erro ao chamar a API STC: {e}. Mantendo os últimos dados.")
    else:
        print("⏳ API STC chamada recentemente. Retornando últimos dados armazenados.")

    # 🔥 Se `ultima_resposta_stc` for None ou uma lista vazia, mantém os últimos dados salvos
    if not ultima_resposta_stc:
        print("⚠️ Nenhum dado STC válido encontrado. Mantendo últimos dados salvos.")
        ultima_resposta_stc = ultima_resposta_stc if ultima_resposta_stc else []  # 🔥 Aqui ele mantém os últimos dados

    # Se houver dispositivos, adiciona o tipo
    for device in ultima_resposta_t42:
        device["type"] = "T42"
    for device in ultima_resposta_stc:
        device["type"] = "STC"

    # 🚧 Cercas geográficas (Mantendo todas as que você criou)
        geofences = [
        {"name": "Posto(1)Primario", "center": [-22.10141479570105, -47.8242335993846], "radius": 5000},  # 5 km
        {"name": "posto(1) Secundario", "center": [-22.10141479570105, -47.8242335993846], "radius": 150},  # 100m
        {"name": "Posto(2)Primario", "center": [ -21.775,  -47.5381], "radius": 5000},  # 5 km
        {"name": "posto(2) Secundario", "center": [ -21.775,  -47.5381],"radius": 150},  # 100m
        {"name": "Posto(3)Primario", "center": [ -21.3648,  -48.7574], "radius": 5000},  # 5 km
        {"name": "posto(3) Secundario", "center": [ -21.3648,  -48.7574],"radius": 200},  # 100m
        {"name": "Posto(4)Primario", "center": [ -20.5542,  -49.7085], "radius": 5000},  # 5 km
        {"name": "posto(4) Secundario", "center": [ -20.5542,  -49.7085],"radius": 200},  # 100m
        {"name": "Posto(5)Primario", "center": [ -20.5334,  -47.846], "radius": 5000},  # 5 km
        {"name": "posto(5) Secundario", "center": [ -20.5334,  -47.846],"radius": 200},  # 100m
        {"name": "Posto(6)Primario", "center": [ -18.8786,  -49.0557], "radius": 5000},  # 5 km
        {"name": "posto(6) Secundario", "center": [ -18.8786,  -49.0557],"radius": 200},  # 100m
        {"name": "Posto(7)Primario", "center": [  -18.661527,  -48.161337], "radius": 5000},  # 5 km
        {"name": "posto(7) Secundario", "center": [  -18.661527,  -48.161337],"radius": 200},  # 100m
        
    ]

    return JsonResponse({
        "t42_devices": ultima_resposta_t42,
        "stc_devices": ultima_resposta_stc,  # 🔥 SEMPRE retorna os últimos dados, nunca []
        "geofences": geofences
    })


def mapa_view(request):
    """Renderiza o template do mapa"""
    return render(request, "mapa.html")



class MapaView(TemplateView):
    template_name = "mapa.html"
    
    from django.shortcuts import render
from django.http import JsonResponse


# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Equipamento
from .forms import EquipamentoForm

# ✅ LISTAR EQUIPAMENTOS
from django.db.models.functions import Coalesce
from django.db.models import Value
from django.utils import timezone

from django.db.models.functions import Coalesce
from django.db.models import Value, DateTimeField
from datetime import datetime
from datetime import datetime, timezone
from django.db.models import Value, DateTimeField
from django.db.models.functions import Coalesce
from django.views.generic import ListView
from .models import Equipamento
from django.db.models import F

class EquipamentoListView(ListView):
    model = Equipamento
    template_name = "equipamento_list.html"
    context_object_name = "equipamentos"

    def get_queryset(self):
        # Sem Coalesce, sem loop, sem nada
        return Equipamento.objects.all()


# ✅ CRIAR EQUIPAMENTO
class EquipamentoCreateView(CreateView):
    model = Equipamento
    form_class = EquipamentoForm
    template_name = "equipamento_form.html"
    success_url = reverse_lazy("equipamento_list")  # Redirecionamento após criação

# ✅ EDITAR EQUIPAMENTO
class EquipamentoUpdateView(UpdateView):
    model = Equipamento
    form_class = EquipamentoForm
    template_name = "equipamento_form.html"
    success_url = reverse_lazy("equipamento_list")  # Redirecionamento após edição

# ✅ DELETAR EQUIPAMENTO
class EquipamentoDeleteView(DeleteView):
    model = Equipamento
    template_name = "equipamento_confirm_delete.html"
    success_url = reverse_lazy("equipamento_list")  # Redirecionamento após exclusão

# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Equipamento

class dashboard(ListView):
    model = Equipamento
    template_name = "relatorios.html"
    context_object_name = "equipamentos"  # Nome da variável no template
    ordering = ["-data_insercao"]  # Ordenação por data mais recente
    
    def get_queryset(self):
        equipamentos = Equipamento.objects.all()
        for equipamento in equipamentos:
            equipamento.atualizar_status_pela_localizacao()
        return equipamentos


from django.http import JsonResponse
from .models import Equipamento

from django.http import JsonResponse
from .models import Equipamento

def lista_equipamentos_api(request):
    # Obtém todos os equipamentos e converte para dicionários
    equipamentos = Equipamento.objects.all().values()
    # Retorna como JSON (list() para poder passar no JsonResponse)
    return JsonResponse(list(equipamentos), safe=False)





from django.http import JsonResponse
from .models import Equipamento
import math

# Se quiser usar a mesma lógica de distância do Leaflet, pode instequialar geopy ou você mesmo cria a fórmula
# ou faz um "mock" da distanceTo. Aqui, vamos usar a própria lógica do Leaflet se quiser,
# mas seria preciso instalar e importar ou escrever uma função de Haversine. 
# Para simplificar, usarei a fórmula de Haversine manualmente.

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calcula distância (em metros) usando a fórmula de Haversine
    """
    R = 6371_000  # raio da Terra ~ 6371 km em metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # retorna metros
    return R * c

CERCAS = [
    { "nome": "Carmocoffe", "coordenadas": [-21.6319, -45.2740], "raio": 8000, "cor": "red" },
    { "nome": "Alto Cafezal", "coordenadas": [-18.9484, -47.0058], "raio": 8000, "cor": "red" },
    { "nome": "BOURBON SPECIALTY COFFEES", "coordenadas": [-21.7804, -46.5690], "raio": 8000, "cor": "red" },
    { "nome": "COOXUPÉ", "coordenadas": [-21.2937, -46.7222], "raio": 500,  "cor": "red" },
    { "nome": "EXPOCACCER", "coordenadas": [-18.9455, -47.0071], "raio": 8000, "cor": "red" },
    { "nome": "NKG", "coordenadas": [-21.5771, -45.4721], "raio": 5800, "cor": "red" },
    { "nome": "VELOSO COFFEE", "coordenadas": [-18.9981, -46.3011], "raio": 8000, "cor": "red" },
    { "nome": "ANTUERPIA", "coordenadas": [51.2639, 4.41496], "raio": 8000, "cor": "green" },
    { "nome": "porto", "coordenadas": [51.3032, 4.2824], "raio": 8000, "cor": "green" },
    { "nome": "VOLCAFÉ", "coordenadas": [-21.5743, -45.4389], "raio": 8000, "cor": "red" },
    { "nome": "BREMEN", "coordenadas": [53.1208, 8.7345], "raio": 8000, "cor": "green" },
    { "nome": "AVENCHES", "coordenadas": [46.8938, 7.0514], "raio": 8000, "cor": "green" },
    { "nome": "BREMENPORT", "coordenadas": [53.0584, 8.8966], "raio": 8000, "cor": "green" },
    { "nome": "BREMENPORT2", "coordenadas": [53.1258, 8.7190], "raio": 8000, "cor": "green" },
    { "nome": "ROMONT", "coordenadas": [46.6806, 6.9051], "raio": 8000, "cor": "green" },
    { "nome": "BARCELONA", "coordenadas": [41.3504, 2.1635], "raio": 8000, "cor": "green" },
    { "nome": "orbe", "coordenadas": [46.7266, 6.5365], "raio": 8000, "cor": "green" }
]

def verificar_status(lat, lon):
    """
    Retorna 'Na Fazenda' se cor=red, 'No Destino' se cor=green, ou 'Em Viagem'
    """
    if lat is None or lon is None:
        return "Sem Coord."

    for cerca in CERCAS:
        lat_cerca, lon_cerca = cerca["coordenadas"]
        dist_metros = distance_km(lat, lon, lat_cerca, lon_cerca)  # retorna metros
        if dist_metros <= cerca["raio"]:
            return "Na Fazenda" if cerca["cor"] == "red" else "No Destino"
    return "Em Viagem"

def lista_equipamentos_api(request):
    """
    Retorna JSON de equipamentos com status calculado
    """
    equipamentos = Equipamento.objects.all()
    data = []
    for eq in equipamentos:
        # Calcule o status para cada eq
        lat = eq.latitude
        lon = eq.longitude
        status = verificar_status(lat, lon)

        data.append({
            "id": eq.id,
            "cliente": eq.cliente,
            "latitude": lat,
            "longitude": lon,
            "status": status,
            # inclua outros campos que desejar
        })

    return JsonResponse(data, safe=False)





from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Equipamento
from .serializers import EquipamentoSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Equipamento
from .serializers import EquipamentoSerializer

class EquipamentoListAPIView(APIView):
    def get(self, request):
        equipamentos = Equipamento.objects.all()
        serializer = EquipamentoSerializer(equipamentos, many=True)
        return Response(serializer.data)

# views.py
from django.http import JsonResponse
from .models import Equipamento

def lista_equipamentos_api(request):
    equipamentos = Equipamento.objects.all().values()
    return JsonResponse(list(equipamentos), safe=False)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Equipamento

@csrf_exempt  # Permite requisições sem CSRF Token (não recomendado para produção sem proteção extra)
def atualizar_equipamento(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Pega os dados enviados via JSON
            
            equipamento = Equipamento.objects.get(identificador=data["identificador"])
            equipamento.status_operacao = data["status"]
            equipamento.save()

            return JsonResponse({"mensagem": "Equipamento atualizado com sucesso!"}, status=200)
        except Equipamento.DoesNotExist:
            return JsonResponse({"erro": "Equipamento não encontrado."}, status=404)
        except Exception as e:
            return JsonResponse({"erro": str(e)}, status=500)
    return JsonResponse({"erro": "Método não permitido"}, status=405)

import requests
import urllib3


# Desabilita o aviso de requisições HTTPS sem verificação de certificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
from django.shortcuts import render
from django.views import View
import requests
from concurrent.futures import ThreadPoolExecutor
from django.views import View
from django.shortcuts import render

def fetch_events(viag_codigo, headers):
    """Função auxiliar para buscar eventos de uma viagem."""
    url_eventos = "https://trafegus.over-haul.com/ws_rest/public/api/eventos"
    params_eventos = {
        "UltCodigo": 1,
        "CodViag": str(viag_codigo)
    }
    response_eventos = requests.get(url_eventos, headers=headers, params=params_eventos, verify=False)
    response_eventos.raise_for_status()
    return response_eventos.json()

class TrafegusVeiculoView(View):
    def get(self, request, *args, **kwargs):
        # 1) Credenciais
        credentials = "V1NfR09MREVOU0FUOk9WRVJIQVVMLjIwMjU="
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
            "X-App-Trafegus": "777"
        }

        # 2) URL e parâmetros para buscar viagens
        url_viagens = "https://trafegus.over-haul.com/ws_rest/public/api/viagem"
        params_viagens = {
            "EmbarcadorDoc": "61064929000179"  # CNPJ
        }

        try:
            # --- A) Primeira requisição: Viagens ---
            response_viagens = requests.get(url_viagens, headers=headers, params=params_viagens, verify=False)
            response_viagens.raise_for_status()
            data = response_viagens.json()

            # Se o JSON retornar algo como {"error": "..."}
            if "error" in data:
                return render(request, "ultima_posicoes.html", {"error": data["error"]})

            # Lista de viagens
            viagens = data.get("viagens", [])

            # --- B) Montar dicionário de "futures" para cada viag_codigo ---
            futures_dict = {}  # { viag_codigo: (viagem, future) }

            with ThreadPoolExecutor(max_workers=10) as executor:
                for viagem in viagens:
                    valor_frete_list = viagem.get("valor_frete", [])
                    if not valor_frete_list:
                        # Se não tem valor_frete, já define "eventos" vazio
                        viagem["eventos"] = []
                        continue

                    viag_codigo = valor_frete_list[0].get("viag_codigo")
                    if viag_codigo:
                        # Dispara a requisição em paralelo
                        future = executor.submit(fetch_events, viag_codigo, headers)
                        # Associa a future a este código de viagem
                        futures_dict[viag_codigo] = (viagem, future)
                    else:
                        viagem["eventos"] = []

            # --- C) Consumir os resultados (eventos) de cada future ---
            for viag_codigo, (viagem, future) in futures_dict.items():
                try:
                    data_eventos = future.result()  # Bloqueia até terminar a requisição
                except requests.RequestException:
                    # Se der erro, eventos = []
                    viagem["eventos"] = []
                    continue

                # Agora filtra e guarda no dicionário da viagem
                todos_eventos = data_eventos.get("eventos", [])
                viagem["eventos"] = todos_eventos

            # Monta o contexto e renderiza
            context = {"viagens": viagens}

        except requests.RequestException as e:
            context = {"error": f"Erro na requisição: {str(e)}"}
        except ValueError:
            context = {"error": "Erro ao processar a resposta JSON"}

        return render(request, "ultima_posicoes.html", context)
