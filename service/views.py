from django.shortcuts import render

from django.views.generic import TemplateView,CreateView
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin

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


def mapa_view2(request):
    """Renderiza o template do mapa"""
    return render(request, "mapa2.html")



class MapaView2(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "mapa2.html"
    permission_required = "empresas.add_empresasmodels"
    
    
    
    

import requests
from django.shortcuts import render

def ultima_posicao_veiculos(request):
    # URL do endpoint para retornar a última posição de cada veículo
    api_url = "http://ip.do.cliente:porta/ws_rest/public/api/ultimaPosicaoVeiculo"
    transportador = "29872062000175"
    # Parâmetros da requisição (exemplo: IdPosicao = 0 indica início)
    params = {
        "Documento": transportador,
        "IdPosicao": 0,  # Ponto de partida para a listagem (pode ser ajustado conforme necessário)
        # Você pode incluir outros parâmetros, como filtro por transportador, se necessário
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()  # Dados retornados em JSON pela API
    except requests.RequestException as e:
        # Em caso de erro na requisição, encapsulamos a mensagem de erro
        data = {"error": str(e)}
    
    # Supomos que a API retorna os dados das posições em uma chave "Posicao"
    posicoes = data.get("Posicao", [])
    
    # Enviamos as posições para o template
    context = {
        "posicoes": posicoes
    }
    return render(request, "ultima_posicoes.html", context)
