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

    # 🚧 Cercas geográficas (sempre definidas)
    geofences = [
        {"name": "Posto(1)Primario", "center": [-22.10141479570105, -47.8242335993846], "radius": 5000},
        {"name": "posto(1) Secundario", "center": [-22.10141479570105, -47.8242335993846], "radius": 150},
        {"name": "Posto(2)Primario", "center": [ -21.775,  -47.5381], "radius": 5000},
        {"name": "posto(2) Secundario", "center": [ -21.775,  -47.5381],"radius": 150},
        {"name": "Posto(3)Primario", "center": [ -21.3648,  -48.7574], "radius": 5000},
        {"name": "posto(3) Secundario", "center": [ -21.3648,  -48.7574],"radius": 200},
        {"name": "Posto(4)Primario", "center": [ -20.5542,  -49.7085], "radius": 5000},
        {"name": "posto(4) Secundario", "center": [ -20.5542,  -49.7085],"radius": 200},
        {"name": "Posto(5)Primario", "center": [ -20.5334,  -47.846], "radius": 5000},
        {"name": "posto(5) Secundario", "center": [ -20.5334,  -47.846],"radius": 200},
        {"name": "Posto(6)Primario", "center": [ -18.8786,  -49.0557], "radius": 5000},
        {"name": "posto(6) Secundario", "center": [ -18.8786,  -49.0557],"radius": 200},
        {"name": "Posto(7)Primario", "center": [  -18.661527,  -48.161337], "radius": 5000},
        {"name": "posto(7) Secundario", "center": [  -18.661527,  -48.161337],"radius": 200},
    ]

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
                try:
                    stc_raw_data = stc_response.json()
                except Exception as e:
                    print(f"Erro ao decodificar JSON da API STC: {e}")
                    stc_raw_data = {}
                if "data" in stc_raw_data and stc_raw_data["data"]:
                    ultima_resposta_stc = stc_raw_data["data"]
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
        ultima_resposta_stc = ultima_resposta_stc if ultima_resposta_stc else []

    # Se houver dispositivos, adiciona o tipo
    for device in ultima_resposta_t42:
        device["type"] = "T42"
    for device in ultima_resposta_stc:
        device["type"] = "STC"

    # DEBUG: Mostra os valores atuais no console
    print("\n==== DEBUG get_devices_data ====")
    print(f"STC devices: {len(ultima_resposta_stc)}")
    for d in ultima_resposta_stc:
        print(d)
    print(f"T42 devices: {len(ultima_resposta_t42)}")
    for d in ultima_resposta_t42:
        print(d)
    print(f"Geofences: {len(geofences)}")
    for g in geofences:
        print(g)
    print("==============================\n")

    # Sempre retorna JSON válido
    return JsonResponse({
        "t42_devices": ultima_resposta_t42,
        "stc_devices": ultima_resposta_stc,
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
    url_eventos = "https://trafegus.over-haul.com/ws/getClientVehicles"
    params_eventos = {
        "UltCodigo": 1,
        "CodViag": str(viag_codigo)
    }
    response_eventos = requests.get(url_eventos, headers=headers, params=params_eventos, verify=False)
    response_eventos.raise_for_status()
    return response_eventos.json()


class TrafegusVeiculoView(View):
    def get(self, request, *args, **kwargs):
        try:
            # API credentials
            credentials = {
                "key": "17bfae24cd65753c0a577e8f65a405cf",
                "user": "stc",
                "pass": "e725df0794b817f84db1e813c3512b21"
            }
            headers = {
                "Content-Type": "application/json",
                "X-App-Trafegus": "777"
            }
            url = "https://trafegus.over-haul.com/ws/getClientVehicles"
            
            # --- CERCAS ---
            cercas = [
                {"nome": "Posto(1)Primario", "latitude": -22.10141479570105, "longitude": -47.8242335993846, "raio": 5000},
                {"nome": "posto(1) Secundario", "latitude": -22.10141479570105, "longitude": -47.8242335993846, "raio": 150},
                {"nome": "Posto(2)Primario", "latitude": -21.775, "longitude": -47.5381, "raio": 5000},
                {"nome": "posto(2) Secundario", "latitude": -21.775, "longitude": -47.5381, "raio": 150},
                {"nome": "Posto(3)Primario", "latitude": -21.3648, "longitude": -48.7574, "raio": 5000},
                {"nome": "posto(3) Secundario", "latitude": -21.3648, "longitude": -48.7574, "raio": 200},
                {"nome": "Posto(4)Primario", "latitude": -20.5542, "longitude": -49.7085, "raio": 5000},
                {"nome": "posto(4) Secundario", "latitude": -20.5542, "longitude": -49.7085, "raio": 200},
                {"nome": "Posto(5)Primario", "latitude": -20.5334, "longitude": -47.846, "raio": 5000},
                {"nome": "posto(5) Secundario", "latitude": -20.5334, "longitude": -47.846, "raio": 200},
                {"nome": "Posto(6)Primario", "latitude": -18.8786, "longitude": -49.0557, "raio": 5000},
                {"nome": "posto(6) Secundario", "latitude": -18.8786, "longitude": -49.0557, "raio": 200},
                {"nome": "Posto(7)Primario", "latitude": -18.661527, "longitude": -48.161337, "raio": 5000},
                {"nome": "posto(7) Secundario", "latitude": -18.661527, "longitude": -48.161337, "raio": 200},
            ]
            
            # --- EQUIPAMENTOS DO BANCO ---
            equipamentos_qs = Equipamento.objects.all()
            equipamentos = []
            for eq in equipamentos_qs:
                if eq.latitude and eq.longitude:
                    equipamentos.append({
                        "nome": eq.identificador or eq.cliente or f"ID {eq.id}",
                        "latitude": float(eq.latitude),
                        "longitude": float(eq.longitude)
                    })
            
            # --- VEÍCULOS (API) ---
            veiculos = []
            try:
                response = requests.post(url, json=credentials, headers=headers, verify=False)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    for v in data.get("data", []):
                        try:
                            lat = float(v.get("latitude", 0))
                            lon = float(v.get("longitude", 0))
                            if lat != 0 and lon != 0:  # Só adiciona se tiver coordenadas válidas
                                veiculos.append({
                                    "placa": v.get("plate", ""),
                                    "motorista": v.get("driverName", ""),
                                    "status": v.get("status", ""),
                                    "latitude": lat,
                                    "longitude": lon,
                                    "empresa": get_empresa_por_placa(v.get("plate", "")),
                                    "tipo": "Trafegus"
                                })
                                print(f"Veículo adicionado: {v.get('plate', '')} em {lat}, {lon}")
                        except (ValueError, TypeError) as e:
                            print(f"Erro ao processar veículo {v.get('plate', '')}: {str(e)}")
                            continue
                else:
                    print("API Trafegus erro:", data.get("error"))
            except Exception as e:
                print("Erro ao buscar veículos da API:", e)
            
            # Adiciona veículos STC
            stc_veiculos = get_stc_vehicle_positions()
            for v in stc_veiculos:
                if v.get("latitude") and v.get("longitude"):
                    try:
                        lat = float(v.get("latitude"))
                        lon = float(v.get("longitude"))
                        if lat != 0 and lon != 0:
                            veiculos.append({
                                "placa": v.get("nome", ""),
                                "motorista": "STC",
                                "status": v.get("detalhes", {}).get("status", ""),
                                "latitude": lat,
                                "longitude": lon,
                                "empresa": get_empresa_por_placa(v.get("nome", "")),
                                "tipo": "STC"
                            })
                            print(f"Veículo STC adicionado: {v.get('nome', '')} em {lat}, {lon}")
                    except (ValueError, TypeError) as e:
                        print(f"Erro ao processar veículo STC {v.get('nome', '')}: {str(e)}")
                        continue
            
            print(f"Total de veículos processados: {len(veiculos)}")
            
            # Se for uma requisição AJAX, retorna JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "cercas": cercas,
                    "equipamentos": equipamentos,
                    "veiculos": veiculos
                })
            
            # Se for uma requisição normal, renderiza o template
            return render(request, "ultima_posicoes.html", {
                "cercas": cercas,
                "equipamentos": equipamentos,
                "veiculos": veiculos,
                "total_veiculos": len(veiculos),
                "veiculos_em_cercas": len([v for v in veiculos if any(
                    check_geofence(v["latitude"], v["longitude"], {"center": [c["latitude"], c["longitude"]], "radius": c["raio"]})
                    for c in cercas
                )])
            })
            
        except Exception as e:
            print("Erro na view:", str(e))
            return JsonResponse({"success": False, "error": str(e)}, status=500)

def get_stc_vehicle_positions():
    """Obtém as posições dos veículos da API STC"""
    print("\n=== INICIANDO CHAMADA API STC ===")
    url = "http://ap3.stc.srv.br/integration/prod/ws/getVehiclePositions"
    payload = {
        "key": "d548f2c076480dcc2bd69fcbf8e6be61",
        "user": "quality.paradasegura",
        "pass": "6b25cff77f9bad60a73fa81daa7d06ae"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            veiculos = []
            for v in data.get("data", []):
                try:
                    # Converte latitude e longitude para float
                    lat = float(v.get("latitude", 0))
                    lon = float(v.get("longitude", 0))
                    
                    # Só adiciona se tiver coordenadas válidas
                    if lat != 0 and lon != 0:
                        # Usa o endereço que já vem da API
                        endereco = v.get("address", "Endereço não disponível")
                        
                        veiculo = {
                            "nome": v.get("plate", ""),  # Nome para exibição no mapa
                            "latitude": lat,
                            "longitude": lon,
                            "tipo": "STC",  # Identificador para o mapa
                            "endereco": endereco,  # Endereço já formatado
                            "detalhes": {
                                "placa": v.get("plate", ""),
                                "modelo": v.get("deviceModel", ""),
                                "endereco": endereco,
                                "data": v.get("date", ""),
                                "ignicao": v.get("ignition", ""),
                                "velocidade": v.get("speed", "0"),
                                "bateria": v.get("batteryPercentual", ""),
                                "gpsFix": v.get("gpsFix", "0"),
                                "originPosition": v.get("originPosition", "")
                            },
                            "empresa": get_empresa_por_placa(v.get("plate", "")),
                            "tipo": "STC"
                        }
                        veiculos.append(veiculo)
                        print(f"Veículo adicionado: {veiculo['nome']} em {lat}, {lon}")
                except (ValueError, TypeError) as e:
                    print(f"Erro ao processar veículo {v.get('plate', '')}: {str(e)}")
                    continue

            print(f"Total de veículos STC processados: {len(veiculos)}")
            return veiculos
        else:
            print("API STC retornou erro:", data.get("error"))
            return []
            
    except Exception as e:
        print("\n❌ ERRO AO BUSCAR VEÍCULOS STC:")
        print(f"Tipo do erro: {type(e)}")
        print(f"Mensagem: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Resposta da API: {e.response.text}")
        return []

class STCVeiculosAPIView(View):
    """View para retornar as últimas posições dos veículos da STC em JSON"""
    def get(self, request, *args, **kwargs):
        try:
            veiculos = get_stc_vehicle_positions()
            return JsonResponse({
                "success": True,
                "veiculos": veiculos,
                "total": len(veiculos),
                "timestamp": time.time()
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)

def minha_view(request):
    """View de exemplo para tratamento de erros"""
    try:
        # Implementar lógica específica aqui
        return JsonResponse({"ok": True, "dados": {}})
    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)}, status=500)

def mapa_stc(request):
    return render(request, 'mapa_stc.html')

def get_empresa_por_placa(placa):
    # Adapte para sua lógica real
    if placa in ["RUR3I87", "PZZ9737"]:  # placas da Corteva
        return "Corteva"
    elif placa in ["OUTRA1", "OUTRA2"]:  # placas da Comandolog
        return "Comandolog"
    else:
        return "Desconhecida"
