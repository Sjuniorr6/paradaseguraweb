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

    def atualizar_stc(self, dados):
        if dados:
            self._stc_cache = dados
            self._ultima_atualizacao_stc = time.time()

    def atualizar_t42(self, dados):
        if dados:
            self._t42_cache = dados
            self._ultima_atualizacao_t42 = time.time()

    def obter_stc(self):
        return self._stc_cache

    def obter_t42(self):
        return self._t42_cache

    def tempo_desde_atualizacao_stc(self):
        return time.time() - self._ultima_atualizacao_stc

    def tempo_desde_atualizacao_t42(self):
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

        # Busca a placa corretamente (trafegus pode ser 'plate', 'placa' ou dentro de 'detalhes')
        placa = (
            vehicle_data.get('placa') or
            vehicle_data.get('plate') or
            (vehicle_data.get('detalhes', {}).get('placa') if vehicle_data.get('detalhes') else None) or
            'N/A'
        )
        # Busca status corretamente
        status = (
            vehicle_data.get('statusCarga') or
            vehicle_data.get('status') or
            (vehicle_data.get('detalhes', {}).get('statusCarga') if vehicle_data.get('detalhes') else None) or
            (vehicle_data.get('detalhes', {}).get('status') if vehicle_data.get('detalhes') else None) or
            'N/A'
        )

        # Envia para todos os usuários conectados
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "notification_message",
                "message": {
                    "type": "geofence",
                    "title": "Veículo dentro da cerca",
                    "text": f"Veículo {placa} está dentro da cerca {geofence_name}",
                    "vehicle": vehicle_data,
                    "image": image_url,
                    "geofence_type": "Primario" if "Primario" in geofence_name else "Secundario",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
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
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "notification_message",
                "message": {
                    "type": "geofence_exit",
                    "title": "Veículo saiu da cerca",
                    "text": f"Veículo {vehicle_data.get('placa', 'N/A')} saiu da cerca {geofence_name}",
                    "vehicle": vehicle_data,
                    "image": image_url,
                    "geofence_type": "Saida",
                    "status": vehicle_data.get('statusCarga', 'N/A'),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    except Exception as e:
        print(f"Erro ao enviar notificação de saída: {str(e)}")
        # Continua a execução mesmo se falhar a notificação

#==============
def get_devices_data(request):
    global ultima_chamada_stc, ultima_resposta_stc, ultima_chamada_t42, ultima_resposta_t42

    # Inicializa as variáveis globais com os dados do cache persistente
    ultima_resposta_stc = cache_persistente.obter_stc()
    ultima_resposta_t42 = cache_persistente.obter_t42()

    t42_updated = False
    stc_updated = False

    tempo_atual = time.time()
    
    # Verifica se é hora de atualizar os dados T42 (a cada 120 segundos)
    if tempo_atual - cache_persistente.tempo_desde_atualizacao_t42() >= 120:
        try:
            params_t42 = {
                "commandname": "get_last_transmits",
                "user": T42_USER,
                "pass": T42_PASS,
                "format": "json"
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            t42_response = requests.get(
                T42_API_URL, 
                params=params_t42, 
                verify=False, 
                timeout=30,
                headers=headers
            )
            
            if t42_response.status_code == 200:
                try:
                    t42_data = t42_response.json()
                    if isinstance(t42_data, list):
                        processed_t42_data = []
                        for device in t42_data:
                            if isinstance(device, dict):
                                processed_device = {
                                    'type': 'T42',
                                    'latitude': device.get('latitude', 0),
                                    'longitude': device.get('longitude', 0),
                                    'plate': device.get('plate', 'N/A'),
                                    'speed': device.get('speed', 0),
                                    'direction': device.get('direction', 0),
                                    'ignition': device.get('ignition', False),
                                    'last_update': device.get('last_update', ''),
                                    'unitnumber': device.get('unitnumber', ''),
                                    'status': device.get('status', '')
                                }
                                processed_t42_data.append(processed_device)
                        
                        # Atualiza o cache persistente com os novos dados
                        cache_persistente.atualizar_t42(processed_t42_data)
                        ultima_resposta_t42 = processed_t42_data
                        t42_updated = True
                        print(f"✅ API T42 atualizada com {len(processed_t42_data)} dispositivos.")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Erro ao decodificar resposta T42: {str(e)}")
        except requests.RequestException as e:
            print(f"⚠️ Erro na requisição T42: {str(e)}")

    # Verifica se é hora de atualizar os dados STC (a cada 60 segundos)
    if tempo_atual - cache_persistente.tempo_desde_atualizacao_stc() >= 60:
        try:
            payload_stc = {
                "key": STC_KEY,
                "user": STC_USER,
                "pass": STC_PASS
            }
            
            stc_response = requests.post(STC_API_URL, json=payload_stc, verify=False)
            
            if stc_response.status_code == 200:
                try:
                    stc_data = stc_response.json()
                    if stc_data.get("success") is True and stc_data.get("data"):
                        # Atualiza o cache persistente com os novos dados
                        cache_persistente.atualizar_stc(stc_data["data"])
                        ultima_resposta_stc = stc_data["data"]
                        stc_updated = True
                        print("✅ API STC atualizada com novos dados.")
                    else:
                        print(f"⚠️ API STC retornou resposta inválida: {stc_data}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ Erro ao decodificar resposta STC: {str(e)}")
        except requests.RequestException as e:
            print(f"⚠️ Erro na requisição STC: {str(e)}")

    # Busca dados da Trafegus
    trafegus_vehicles = fetch_trafegus_vehicles()
    
    # Adiciona o tipo para cada dispositivo
    for device in ultima_resposta_t42:
        device["type"] = "T42"
    for device in ultima_resposta_stc:
        device["type"] = "STC"
        device["placa"] = device.get('placa') or device.get('plate') or device.get('name') or device.get('deviceId')
        device["statusCarga"] = device.get('statusCarga') or device.get('status') or device.get('ignicao')
    for device in trafegus_vehicles:
        device["type"] = "Trafegus"

    # Log de debug
    print("\n==== DEBUG get_devices_data ====")
    print(f"STC devices: {len(ultima_resposta_stc)}")
    for d in ultima_resposta_stc:
        print(d)
    print(f"T42 devices: {len(ultima_resposta_t42)}")
    for d in ultima_resposta_t42:
        print(d)
    print(f"Trafegus devices: {len(trafegus_vehicles)}")
    for d in trafegus_vehicles:
        print(d)
    print("==============================\n")

    # Combina todos os veículos
    all_devices = ultima_resposta_t42 + ultima_resposta_stc + trafegus_vehicles

    # Verifica geofences para cada dispositivo
    for device in all_devices:
        processed_device = {
            'type': device.get('type'),
            'latitude': device.get('latitude') or device.get('lat'),
            'longitude': device.get('longitude') or device.get('lon'),
            'placa': device.get('plate') or device.get('placa') or (device.get('detalhes', {}).get('placa') if device.get('detalhes') else None) or device.get('unitnumber'),
            'statusCarga': device.get('statusCarga') or device.get('status'),
            'detalhes': device.get('detalhes', {})
        }
        
        if device.get('type') == 'Trafegus':
            processed_device['motorista'] = device.get('motorista')
            processed_device['descricaoLocal'] = device.get('endereco')
            processed_device['dataPosicao'] = device.get('datetime_utc')

        check_vehicle_geofence(processed_device, geofences)

    return JsonResponse({
        "t42_devices": ultima_resposta_t42,
        "stc_devices": ultima_resposta_stc,
        "trafegus_vehicles": trafegus_vehicles,
        "all_devices": all_devices,
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

    vehicle_id = vehicle_data.get('placa')
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
