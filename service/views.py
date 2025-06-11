from django.shortcuts import render

from django.views.generic import TemplateView,CreateView
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
from math import radians, sin, cos, sqrt, atan2
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from pparada.models import paradasegura
from datetime import datetime, timedelta
import os
from service.models import Geofence, UserGeofence
import time
import threading

# Create your views here.
T42_API_URL = "https://mongol.brono.com/mongol/api.php"
T42_USER = "gs_paradasegura"
T42_PASS = "GGS@20xx"

# Inicializa a variável global fora da função
ultima_chamada_stc = None
ultima_resposta_stc = None
ultima_chamada_t42 = None
ultima_resposta_t42 = None

# 🔥 Variáveis globais para armazenar os últimos dados válidos
ultima_resposta_trafegus = []  # Adicionado para cache da Trafegus

# Cache para armazenar última posição conhecida dos veículos
veiculos_cache = {}

# Cache persistente para armazenar os últimos dados válidos
class CachePersistente:
    def __init__(self):
        self._stc_cache = []
        self._t42_cache = []
        self._ultima_atualizacao_stc = 0
        self._ultima_atualizacao_t42 = 0
        self._lock = threading.Lock()  # Adiciona lock para thread safety

    def atualizar_stc(self, dados):
        if dados:
            with self._lock:
                self._stc_cache = dados
                self._ultima_atualizacao_stc = time.time()
                print(f"Cache STC atualizado com {len(dados)} dispositivos")

    def atualizar_t42(self, dados):
        if dados:
            with self._lock:
                self._t42_cache = dados
                self._ultima_atualizacao_t42 = time.time()
                print(f"Cache T42 atualizado com {len(dados)} dispositivos")

    def obter_stc(self):
        with self._lock:
            return self._stc_cache.copy()  # Retorna uma cópia para evitar modificações acidentais

    def obter_t42(self):
        with self._lock:
            return self._t42_cache.copy()  # Retorna uma cópia para evitar modificações acidentais

    def tempo_desde_atualizacao_stc(self):
        with self._lock:
            return time.time() - self._ultima_atualizacao_stc

    def tempo_desde_atualizacao_t42(self):
        with self._lock:
            return time.time() - self._ultima_atualizacao_t42

# Instância global do cache persistente
cache_persistente = CachePersistente()

#==============
def fetch_trafegus_vehicles():
    """
    Função para buscar dados da Trafegus
    """
    documentos = ["61064929000179", "24315867000102"]
    auth = ("WS_GOLDENSAT", "OVERHAUL.2025")
    
    processed_data = []

    for documento in documentos:
        url = f"https://trafegus.over-haul.com/ws_rest/public/api/ultima-posicao-viagem?Documento={documento}"
        
        try:
            response = requests.get(url, auth=auth, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Processa os dados para extrair informações relevantes
            for viagem in data.get("viagem", []):
                posicao = viagem.get("posicoesViagem", {})
                if not posicao:
                    continue
                    
                # Extrai coordenadas da string
                coordenada = posicao.get("coordenada", "")
                lat, lng = None, None
                if coordenada:
                    try:
                        lat, lng = map(float, coordenada.split(","))
                    except (ValueError, AttributeError):
                        continue
                
                if lat is None or lng is None:
                    continue
                    
                status_carga = posicao.get("statusCarga", "").upper()
                if any(status in status_carga for status in ['FINISH', 'FINALIZADO', 'CONCLUIDO', 'ENTREGUE']):
                    continue  # pula veículos finalizados
                
                processed_viagem = {
                    "placa": posicao.get("placa"),
                    "placaCarreta": posicao.get("placaCarreta"),
                    "motorista": posicao.get("motorista"),
                    "statusCarga": posicao.get("statusCarga"),
                    "descricaoLocal": posicao.get("descricaoLocal"),
                    "dataPosicao": posicao.get("dataPosicao"),
                    "latitude": lat,
                    "longitude": lng,
                    "contatoMotorista": posicao.get("contatoMotorista", []),
                    "notasFiscais": posicao.get("notasFiscais", []),
                    "documento": documento,
                    "empresa": posicao.get("empresa", "N/A")
                }
                
                processed_data.append(processed_viagem)
                
        except requests.RequestException as e:
            print(f"Erro ao buscar dados para documento {documento}: {str(e)}")
            continue
    
    return processed_data

#==============
def get_t42_data(request):
    # View para buscar dados brutos da API T42 e retornar como JSON sem filtro
    #==============
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

#==============
def calculate_distance(lat1, lon1, lat2, lon2):
    # Função utilitária para calcular a distância entre dois pontos geográficos (Haversine)
    #==============
    R = 6371000  # Raio da Terra em metros

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

#==============
def check_geofence(vehicle_lat, vehicle_lon, geofence):
    # Função utilitária para verificar se um ponto está dentro de uma cerca geográfica
    center_lat, center_lon = geofence['center']
    radius = geofence['radius']
    
    distance = calculate_distance(
        float(vehicle_lat), 
        float(vehicle_lon), 
        float(center_lat), 
        float(center_lon)
    )
    
    return distance <= radius

#==============
def notify_geofence_event(vehicle_data, geofence_name):
    # Função para enviar notificação quando um veículo entra em uma cerca geográfica
    try:
        channel_layer = get_channel_layer()

        # Determina qual imagem usar baseado no tipo de cerca
        image_url = '/static/images/'
        if 'Primario' in geofence_name:
            image_url += 'circuit-board.png'  # Imagem para cerca primária
        else:
            image_url += 'lock.png'  # Imagem para cerca secundária

        # A placa e o status já vêm padronizados da função get_devices_data
        placa = vehicle_data.get('placa', 'N/A')
        status = vehicle_data.get('statusCarga', 'N/A')

        # Garante que placa e status não sejam vazios para o alerta
        placa_alerta = placa if placa and placa != 'N/A' else 'N/A'
        status_alerta = status if status and status != 'N/A' else 'N/A'

        # Envia para todos os usuários conectados
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "notification_message",
                "title": "Veículo dentro da cerca",
                "text": f"Veículo {placa_alerta} está dentro da cerca {geofence_name}",
                "vehicle": vehicle_data,
                "image": image_url,
                "geofence_type": "Primario" if "Primario" in geofence_name else "Secundario",
                "status": status_alerta,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Erro ao enviar notificação: {str(e)}")
        # Continua a execução mesmo se falhar a notificação

#==============
def notify_geofence_exit_event(vehicle_data, geofence_name):
    # Função para enviar notificação quando um veículo sai de uma cerca geográfica
    try:
        channel_layer = get_channel_layer()
        image_url = '/static/images/lock.png'  # Pode customizar se quiser
        
        # A placa e o status já vêm padronizados da função get_devices_data
        placa = vehicle_data.get('placa', 'N/A')
        status = vehicle_data.get('statusCarga', 'N/A')

        # Garante que placa e status não sejam vazios para o alerta
        placa_alerta = placa if placa and placa != 'N/A' else 'N/A'
        status_alerta = status if status and status != 'N/A' else 'N/A'

        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "notification_message",
                "title": "Veículo saiu da cerca",
                "text": f"Veículo {placa_alerta} saiu da cerca {geofence_name}",
                "vehicle": vehicle_data,
                "image": image_url,
                "geofence_type": "Saida",
                "status": status_alerta,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Erro ao enviar notificação de saída: {str(e)}")
        # Continua a execução mesmo se falhar a notificação

#==============
def get_devices_data(request):
    global ultima_chamada_stc, ultima_resposta_stc, ultima_chamada_t42, ultima_resposta_t42

    print("\n==== INÍCIO get_devices_data ====")

    # Busca dados T42
    try:
        params_t42 = {
            "commandname": "get_last_transmits",
            "user": T42_USER,
            "pass": T42_PASS,
            "format": "json"
        }
        
        print("Buscando dados T42...")
        t42_response = requests.get(
            T42_API_URL, 
            params=params_t42, 
            verify=False, 
            timeout=30
        )
        
        if t42_response.status_code == 200:
            t42_data = t42_response.json()
            if isinstance(t42_data, list):
                for device in t42_data:
                    device['type'] = 'T42'
                ultima_resposta_t42 = t42_data
                cache_persistente.atualizar_t42(t42_data)
                print(f"✅ Dados T42 recebidos: {len(t42_data)} dispositivos")
    except Exception as e:
        print(f"⚠️ Erro ao buscar dados T42: {str(e)}")
        ultima_resposta_t42 = cache_persistente.obter_t42()

    # Busca dados STC
    try:
        payload_stc = {
            "key": STC_KEY,
            "user": STC_USER,
            "pass": STC_PASS
        }
        
        print("Buscando dados STC...")
        stc_response = requests.post(STC_API_URL, json=payload_stc, verify=False, timeout=30)
        
        if stc_response.status_code == 200:
            stc_data = stc_response.json()
            if stc_data.get("success") is True and stc_data.get("data"):
                for device in stc_data["data"]:
                    device['type'] = 'STC'
                ultima_resposta_stc = stc_data["data"]
                cache_persistente.atualizar_stc(stc_data["data"])
                print(f"✅ Dados STC recebidos: {len(stc_data['data'])} dispositivos")
    except Exception as e:
        print(f"⚠️ Erro ao buscar dados STC: {str(e)}")
        ultima_resposta_stc = cache_persistente.obter_stc()

    # Busca dados Trafegus
    print("Buscando dados Trafegus...")
    trafegus_vehicles = fetch_trafegus_vehicles()
    
    # Log de debug
    print("\n==== DEBUG get_devices_data ====")
    print(f"STC devices: {len(ultima_resposta_stc)}")
    print(f"T42 devices: {len(ultima_resposta_t42)}")
    print(f"Trafegus devices: {len(trafegus_vehicles)}")
    print("==============================\n")

    # Combina todos os veículos
    all_devices_raw = ultima_resposta_t42 + ultima_resposta_stc + trafegus_vehicles
    
    standardized_devices = []

    # Padroniza os campos para cada dispositivo e verifica geofences
    for device_raw in all_devices_raw:
        processed_device = {
            'type': device_raw.get('type'),
            'latitude': None, # Inicializa como None, será preenchido abaixo
            'longitude': None, # Inicializa como None, será preenchido abaixo
            'placa': 'N/A',
            'statusCarga': 'N/A',
            'motorista': 'N/A',
            'descricaoLocal': 'N/A',
            'dataPosicao': 'N/A',
            'original_data': device_raw # Mantém os dados originais para referência
        }
        
        if processed_device['type'] == 'Trafegus':
            processed_device['placa'] = device_raw.get('placa') or device_raw.get('plate')
            processed_device['statusCarga'] = device_raw.get('statusCarga') or device_raw.get('status')
            processed_device['latitude'] = float(device_raw.get('latitude')) if device_raw.get('latitude') else None
            processed_device['longitude'] = float(device_raw.get('longitude')) if device_raw.get('longitude') else None
            processed_device['motorista'] = device_raw.get('motorista')
            processed_device['descricaoLocal'] = device_raw.get('descricaoLocal')
            processed_device['dataPosicao'] = device_raw.get('dataPosicao')

        elif processed_device['type'] == 'T42':
            processed_device['placa'] = device_raw.get('device_id')
            processed_device['statusCarga'] = device_raw.get('ignition_status')
            processed_device['latitude'] = float(device_raw.get('lat')) if device_raw.get('lat') else None
            processed_device['longitude'] = float(device_raw.get('lng')) if device_raw.get('lng') else None
            processed_device['dataPosicao'] = device_raw.get('timestamp')
            processed_device['descricaoLocal'] = device_raw.get('address')
            processed_device['speed'] = device_raw.get('speed')
            processed_device['battery_voltage'] = device_raw.get('battery_voltage')

        elif processed_device['type'] == 'STC':
            processed_device['placa'] = device_raw.get('Plate')
            processed_device['statusCarga'] = device_raw.get('LastStatusName')
            processed_device['latitude'] = float(device_raw.get('Latitude')) if device_raw.get('Latitude') else None
            processed_device['longitude'] = float(device_raw.get('Longitude')) if device_raw.get('Longitude') else None
            processed_device['dataPosicao'] = device_raw.get('LastDataHora')
            processed_device['descricaoLocal'] = device_raw.get('Endereco')
            processed_device['temperature'] = device_raw.get('Temperatura')
            processed_device['ignition'] = device_raw.get('Ignition')

        # Apenas adiciona à lista final se tiver placa, latitude e longitude válidos
        if processed_device['placa'] != 'N/A' and processed_device['latitude'] is not None and processed_device['longitude'] is not None:
            standardized_devices.append(processed_device)
            check_vehicle_geofence(processed_device, geofences)
        else:
            print(f"⚠️ Dispositivo ignorado por falta de dados essenciais (placa ou coordenadas): {device_raw.get('type')} - {device_raw}")

    # A resposta JSON deve usar a lista de dispositivos padronizados
    print(f"Total de dispositivos padronizados para envio: {len(standardized_devices)}")

    return JsonResponse({
        "t42_devices": [d for d in standardized_devices if d.get('type') == 'T42'],
        "stc_devices": [d for d in standardized_devices if d.get('type') == 'STC'],
        "trafegus_vehicles": [d for d in standardized_devices if d.get('type') == 'Trafegus'],
        "all_devices": standardized_devices,
        "geofences": geofences
    })


#==============
def mapa_view2(request):
    # View para renderizar o template do mapa2.html
    #==============
    return render(request, "mapa2.html")



#==============
class MapaView2(LoginRequiredMixin,TemplateView):
    # View baseada em classe para renderizar o mapa2.html (com login obrigatório)
    #==============
    template_name = "mapa2.html"
    
    
    
    
    

import requests
from django.shortcuts import render

#==============
def ultima_posicao_veiculos(request):
    # View para buscar e exibir a última posição dos veículos de uma API externa
    #==============
    # URL do endpoint para retornar a última posição de cada veículo
    api_url = "http://ip.do.cliente:porta/ws_rest/public/api/ultimaPosicaoVeiculo"
    transportador = "29872062000175"
    # Parâmetros da requisição (exemplo: IdPosicao = 0 indica início)
    params = {
        "Documento": transportador,
        "IdPosicao": 0,  # Ponto de partida para a listagem (pode ser ajustado conforme necessário)
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
    
    # 🚧 Cercas geográficas (mesmas do get_devices_data)
    geofences = [
        
                {"nome": "Posto Graal Rubi", "latitude": -22.10141479570105, "longitude": -47.8242335993846, "raio": 5000},
                {"nome": "Posto Graal Rubi2", "latitude": -22.10141479570105, "longitude": -47.8242335993846, "raio": 150},
                {"nome": "Posto Da Serra", "latitude": -21.775, "longitude": -47.5381, "raio": 5000},
                {"nome": "Posto Da Serra2", "latitude": -21.775, "longitude": -47.5381, "raio": 150},
                {"nome": "Posto Capixabom", "latitude": -21.3648, "longitude": -48.7574, "raio": 5000},
                {"nome": "posto Capixabom 2", "latitude": -21.3648, "longitude": -48.7574, "raio": 200},
                {"nome": "Posto JN", "latitude": -20.5542, "longitude": -49.7085, "raio": 5000},
                {"nome": "Posto JN2", "latitude": -20.5542, "longitude": -49.7085, "raio": 200},
                {"nome": "Posto Buritizinho", "latitude": -20.5334, "longitude": -47.846, "raio": 5000},
                {"nome": "posto Posto Buritizinho2", "latitude": -20.5334, "longitude": -47.846, "raio": 200},
                {"nome": "Posto Trevao", "latitude": -18.8786, "longitude": -49.0557, "raio": 5000},
                {"nome": "posto Trevao2", "latitude": -18.8786, "longitude": -49.0557, "raio": 200},
                {"nome": "Posto Brasileirao", "latitude": -18.661527, "longitude": -48.161337, "raio": 5000},
                {"nome": "posto Brasileirao2", "latitude": -18.661527, "longitude": -48.161337, "raio": 200},
            ]
            
       
    

    # Filtra apenas os veículos que estão dentro das cercas
    veiculos_em_cercas = []
    for posicao in posicoes:
        # Tente ambos os padrões de chave
        lat = posicao.get('latitude') or posicao.get('Latitude')
        lon = posicao.get('longitude') or posicao.get('Longitude')
        if lat and lon:
            for geofence in geofences:
                if check_geofence(float(lat), float(lon), geofence):
                    posicao['cerca_atual'] = geofence['name']
                    veiculos_em_cercas.append(posicao)
                    break

    context = {
        "posicoes": veiculos_em_cercas,
        "total_veiculos": len(posicoes),
        "veiculos_em_cercas": len(veiculos_em_cercas)
    }
    return render(request, "ultima_posicoes.html", context)






#==============
def trafegus_veiculos(request):
    # View para puxar e processar dados da Trafegus (endpoint público fornecido)
    #==============
    """
    View para puxar dados da Trafegus (endpoint público fornecido)
    """
    documentos = ["61064929000179", "24315867000102"]
    auth = ("WS_GOLDENSAT", "OVERHAUL.2025")
    
    processed_data = {
        "viagens": []
    }

    for documento in documentos:
        url = f"https://trafegus.over-haul.com/ws_rest/public/api/ultima-posicao-viagem?Documento={documento}"
        
        try:
            response = requests.get(url, auth=auth, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Processa os dados para extrair informações relevantes
            for viagem in data.get("viagem", []):
                posicao = viagem.get("posicoesViagem", {})
                if not posicao:
                    continue
                    
                # Extrai coordenadas da string
                coordenada = posicao.get("coordenada", "")
                lat, lng = None, None
                if coordenada:
                    try:
                        lat, lng = map(float, coordenada.split(","))
                    except (ValueError, AttributeError):
                        continue
                
                if lat is None or lng is None:
                    continue
                    
                status_carga = posicao.get("statusCarga", "").upper()
                if any(status in status_carga for status in ['FINISH', 'FINALIZADO', 'CONCLUIDO', 'ENTREGUE']):
                    continue  # pula veículos finalizados
                
                processed_viagem = {
                    "placa": posicao.get("placa"),
                    "placaCarreta": posicao.get("placaCarreta"),
                    "motorista": posicao.get("motorista"),
                    "statusCarga": posicao.get("statusCarga"),
                    "descricaoLocal": posicao.get("descricaoLocal"),
                    "dataPosicao": posicao.get("dataPosicao"),
                    "latitude": lat,
                    "longitude": lng,
                    "contatoMotorista": posicao.get("contatoMotorista", []),
                    "notasFiscais": posicao.get("notasFiscais", []),
                    "documento": documento,
                    "empresa": posicao.get("empresa", "N/A")
                }
                
                processed_data["viagens"].append(processed_viagem)
                
        except requests.RequestException as e:
            print(f"Erro ao buscar dados para documento {documento}: {str(e)}")
            continue
    
    return JsonResponse(processed_data, safe=False)



#==============
def get_rota_latlng(viagem):
    # Função utilitária para extrair rota (lat/lng) de uma viagem
    #==============
    rota = []
    # Origem
    if viagem.get('origem'):
        rota.append({
            'descricao': viagem['origem'].get('vloc_descricao', 'Origem'),
            'lat': float(viagem['origem']['refe_latitude']),
            'lng': float(viagem['origem']['refe_longitude'])
        })

    # Paradas intermediárias
    for local in viagem.get('locais', []):
        if local.get('refe_latitude') and local.get('refe_longitude'):
            rota.append({
                'descricao': local.get('vloc_descricao', 'Parada'),
                'lat': float(local['refe_latitude']),
                'lng': float(local['refe_longitude'])
            })

    # Destino
    if viagem.get('destino'):
        rota.append({
            'descricao': viagem['destino'].get('vloc_descricao', 'Destino'),
            'lat': float(viagem['destino']['refe_latitude']),
            'lng': float(viagem['destino']['refe_longitude'])
        })

    return rota

#==============
def check_vehicle_geofence(vehicle_data, geofences):
    # Função para verificar e notificar se um veículo entrou/saiu de uma cerca
    #==============
    if not vehicle_data.get('latitude') or not vehicle_data.get('longitude'):
        return

    status_carga = str(vehicle_data.get('statusCarga', '')).upper()
    if any(status in status_carga for status in ['FINISH', 'FINALIZADO', 'CONCLUIDO', 'ENTREGUE']):
        return

    # Garante que vehicle_id seja uma string válida para o cache
    vehicle_id = vehicle_data.get('placa')
    if not vehicle_id:
        print(f"⚠️ Veículo sem placa para cache/notificação: {vehicle_data.get('type')} - {vehicle_data.get('original_data', vehicle_data)}")
        return # Não processa veículos sem placa

    current_position = (vehicle_data['latitude'], vehicle_data['longitude'])

    # Descubra em qual cerca (se houver) o veículo está
    current_geofence = None
    for geofence in geofences:
        if check_geofence(vehicle_data['latitude'], vehicle_data['longitude'], geofence):
            current_geofence = geofence['name']
            break

    # Obtém o último estado do veículo do cache
    last_state = veiculos_cache.get(vehicle_id, {})
    last_geofence = last_state.get('geofence')
    last_update = last_state.get('last_update', datetime.min)

    # Verifica se deve emitir um novo alerta
    should_notify = False
    
    # Caso 1: Entrou em uma nova cerca
    if current_geofence and last_geofence != current_geofence:
        should_notify = True
    # Caso 2: Saiu de uma cerca
    elif last_geofence and not current_geofence:
        notify_geofence_exit_event(vehicle_data, last_geofence)
        vehicle_data['current_geofence'] = None
    # Caso 3: Continua na mesma cerca, mas passou tempo suficiente para um novo alerta
    elif current_geofence and (datetime.now() - last_update).total_seconds() >= 300:  # 5 minutos
        should_notify = True

    # Emite o alerta se necessário
    if should_notify:
        notify_geofence_event(vehicle_data, current_geofence)
        vehicle_data['current_geofence'] = current_geofence

    # Atualiza o cache
    veiculos_cache[vehicle_id] = {
        'position': current_position,
        'geofence': current_geofence,
        'last_update': datetime.now(),
        'status': status_carga
    }

# Adiciona as cercas geográficas
geofences = [
    {"name": "Posto Graal Rubi", "center": [-22.10141479570105, -47.8242335993846], "radius": 5000},
    {"name": "Posto Graal Rubi2", "center": [-22.10141479570105, -47.8242335993846], "radius": 150},
    {"name": "Posto Da Serra", "center": [-21.775, -47.5381], "radius": 5000},
    {"name": "Posto Da Serra2", "center": [-21.775, -47.5381], "radius": 150},
    {"name": "Posto Capixabom", "center": [-21.3648, -48.7574], "radius": 5000},
    {"name": "posto Capixabom 2", "center": [-21.3648, -48.7574], "radius": 200},
    {"name": "Posto JN", "center": [-20.5542, -49.7085], "radius": 5000},
    {"name": "Posto JN2", "center": [-20.5542, -49.7085], "radius": 200},
    {"name": "Posto Buritizinho", "center": [-20.5334, -47.846], "radius": 5000},
    {"name": "posto Posto Buritizinho2", "center": [-20.5334, -47.846], "radius": 200},
    {"name": "Posto Trevao", "center": [-18.8786, -49.0557], "radius": 5000},
    {"name": "posto Trevao2", "center": [-18.8786, -49.0557], "radius": 200},
    {"name": "Posto Brasileirao", "center": [-18.661527, -48.161337], "radius": 5000},
    {"name": "posto Brasileirao2", "center": [-18.661527, -48.161337], "radius": 200},
]
