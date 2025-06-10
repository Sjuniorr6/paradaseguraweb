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

# 🔥 Variáveis globais para armazenar os últimos dados válidos
ultima_chamada_t42 = 0
ultima_resposta_t42 = []
ultima_chamada_stc = 0
ultima_resposta_stc = None  # Agora começa como None para evitar sobrescritas erradas
ultima_resposta_trafegus = []  # Adicionado para cache da Trafegus

# Cache para armazenar última posição conhecida dos veículos
veiculos_cache = {}

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
    #==============
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
    #==============
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

    # Loga o alerta no banco de dados
    from notificar.models import AlertLog
    from django.contrib.auth.models import User

    # Cria um alerta para cada usuário ativo
    for user in User.objects.filter(is_active=True):
        pass  # Nada será feito, mas o bloco do for está correto

#==============
def notify_geofence_exit_event(vehicle_data, geofence_name):
    # Função para enviar notificação quando um veículo sai de uma cerca geográfica
    #==============
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

#==============
def get_devices_data(request):
    # View principal: retorna todos os dispositivos (T42, STC, Trafegus) e cercas para o frontend do mapa
    #==============
    global ultima_resposta_t42, ultima_resposta_stc, ultima_resposta_trafegus
    t42_updated = False
    stc_updated = False
    stc_debug_info = {}
    ultima_resposta_t42 = []
    ultima_resposta_stc = []

    # 🔵 API T42 (sempre faz a requisição)
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
    try:
        t42_response = requests.get(
            T42_API_URL, 
            params=params_t42, 
            verify=False, 
            timeout=30,
            headers=headers
        )
        content_type = t42_response.headers.get('content-type', '').lower()
        if t42_response.status_code == 200 and 'application/json' in content_type:
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
                    ultima_resposta_t42 = processed_t42_data
                    t42_updated = True
                    print(f"✅ API T42 atualizada com {len(processed_t42_data)} dispositivos.")
                else:
                    print("⚠️ API T42 retornou JSON inválido.")
            except json.JSONDecodeError as e:
                print(f"⚠️ API T42 retornou resposta inválida: {str(e)}.")
        else:
            print(f"⚠️ API T42 falhou com status {t42_response.status_code} ou tipo de conteúdo inválido ({content_type}).")
    except requests.RequestException as e:
        print(f"⚠️ Erro ao chamar a API T42: {str(e)}.")
    # Se não atualizou, usa o último cache
    if not ultima_resposta_t42:
        print("⚠️ Usando último cache T42!")
        ultima_resposta_t42 = getattr(get_devices_data, '_ultima_resposta_t42_cache', [])
    else:
        get_devices_data._ultima_resposta_t42_cache = ultima_resposta_t42

    # 🔴 API STC (sempre faz a requisição)
    payload_stc = {
        "key": STC_KEY,
        "user": STC_USER,
        "pass": STC_PASS
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    # Variável para cache dos últimos dados válidos da STC
    if not hasattr(get_devices_data, '_ultima_resposta_stc_cache'):
        get_devices_data._ultima_resposta_stc_cache = []

    try:
        stc_response = requests.post(
            STC_API_URL, 
            json=payload_stc, 
            headers=headers,
            verify=False,
            timeout=10  # Reduz o timeout para resposta mais rápida
        )
        content_type = stc_response.headers.get('content-type', '').lower()
        stc_debug_info['status_code'] = stc_response.status_code
        stc_debug_info['content_type'] = content_type
        stc_debug_info['text'] = stc_response.text[:1000]
        if stc_response.status_code == 200 and 'application/json' in content_type:
            try:
                stc_raw_data = stc_response.json()
                stc_debug_info['json'] = stc_raw_data
                processed_stc_data = []
                # Aceita diferentes formatos e processa todos os devices
                devices_list = []
                if isinstance(stc_raw_data, dict):
                    if 'data' in stc_raw_data and isinstance(stc_raw_data['data'], list):
                        devices_list = stc_raw_data['data']
                    else:
                        if get_devices_data._ultima_resposta_stc_cache:
                            ultima_resposta_stc = get_devices_data._ultima_resposta_stc_cache
                            stc_updated = False
                        else:
                            ultima_resposta_stc = []
                        devices_list = []
                elif isinstance(stc_raw_data, list):
                    devices_list = stc_raw_data
                # Processa todos os devices (veículos e iscas)
                isca_ids = []
                for posto in paradasegura.POSTOS_INFO1.values():
                    isca_ids.extend([isca[0] for isca in posto.get('iscas', [])])
                isca_ids = set(isca_ids)
                for device in devices_list:
                    if not isinstance(device, dict):
                        continue
                    lat = device.get('latitude') or device.get('lat')
                    lng = device.get('longitude') or device.get('lng')
                    if not lat or not lng:
                        continue
                    isca = str(device.get('deviceId')) in isca_ids or str(device.get('plate', '')).startswith('RT')
                    # Sempre inclua 'detalhes' para caminhão
                    if not isca and device.get('plate'):
                        processed_device = {
                            'type': 'STC',
                            'latitude': lat,
                            'longitude': lng,
                            'plate': device.get('plate', 'N/A'),
                            'speed': device.get('speed', 0),
                            'direction': device.get('direction', 0),
                            'ignition': device.get('ignition', False),
                            'last_update': device.get('last_update', ''),
                            'deviceId': device.get('deviceId', device.get('unitnumber', device.get('term_numero_terminal', ''))),
                            'status': device.get('status', ''),
                            'batteryPercentual': device.get('batteryPercentual', device.get('bateria', 'N/A')),
                            'main_voltage': device.get('main_voltage', ''),
                            'date': device.get('date', device.get('data_cadastro', '')),
                            'isca': device.get('isca', ''),
                            'detalhes': {
                                'placa': device.get('plate', 'N/A'),
                                'modelo': device.get('modelo', 'N/A'),
                                'status': device.get('status', 'N/A'),
                                'batteryPercentual': device.get('batteryPercentual', 'N/A'),
                                'main_voltage': device.get('main_voltage', 'N/A'),
                                'date': device.get('date', 'N/A'),
                                'isca': device.get('isca', 'N/A'),
                            },
                            'documento': device.get('documento', 'N/A'),
                            'empresa': device.get('empresa', 'N/A')
                        }
                    else:  # Isca
                        processed_device = {
                            'type': 'STC_ISCA',
                            'latitude': lat,
                            'longitude': lng,
                            'plate': device.get('plate', 'N/A'),
                            'speed': device.get('speed', 0),
                            'direction': device.get('direction', 0),
                            'ignition': device.get('ignition', False),
                            'last_update': device.get('last_update', ''),
                            'deviceId': device.get('deviceId', device.get('unitnumber', device.get('term_numero_terminal', ''))),
                            'status': device.get('status', ''),
                            'batteryPercentual': device.get('batteryPercentual', device.get('bateria', 'N/A')),
                            'main_voltage': device.get('main_voltage', ''),
                            'date': device.get('date', device.get('data_cadastro', '')),
                            'isca': device.get('isca', ''),
                            'documento': device.get('documento', 'N/A'),
                            'empresa': device.get('empresa', 'N/A')
                        }
                    processed_stc_data.append(processed_device)
                if processed_stc_data:
                    ultima_resposta_stc = processed_stc_data
                    get_devices_data._ultima_resposta_stc_cache = processed_stc_data
                    stc_updated = True
                    print(f"✅ API STC atualizada com {len(processed_stc_data)} dispositivos (veículos e iscas).")
                else:
                    if get_devices_data._ultima_resposta_stc_cache:
                        ultima_resposta_stc = get_devices_data._ultima_resposta_stc_cache
                        stc_updated = False
                    else:
                        ultima_resposta_stc = []
            except json.JSONDecodeError as e:
                stc_debug_info['json_error'] = str(e)
                print(f"⚠️ API STC retornou resposta inválida: {str(e)}.")
                if get_devices_data._ultima_resposta_stc_cache:
                    ultima_resposta_stc = get_devices_data._ultima_resposta_stc_cache
                    stc_updated = False
                else:
                    return JsonResponse({"error": "A API STC não retornou JSON válido", "stc_debug": stc_response.text[:1000]}, status=502)
        else:
            print(f"⚠️ API STC falhou com status {stc_response.status_code} ou tipo de conteúdo inválido ({content_type}).")
            if get_devices_data._ultima_resposta_stc_cache:
                ultima_resposta_stc = get_devices_data._ultima_resposta_stc_cache
                stc_updated = False
            else:
                return JsonResponse({"error": "A API STC não retornou JSON válido", "stc_debug": stc_response.text[:1000]}, status=502)
    except requests.RequestException as e:
        stc_debug_info['request_exception'] = str(e)
        print(f"⚠️ Erro ao chamar a API STC: {str(e)}.")
        if get_devices_data._ultima_resposta_stc_cache:
            ultima_resposta_stc = get_devices_data._ultima_resposta_stc_cache
            stc_updated = False
        else:
            return JsonResponse({"error": "Erro ao chamar a API STC", "stc_debug": str(e)}, status=502)

    # 🚛 API Trafegus
    trafegus_data = []
    documentos = ["61064929000179", "24315867000102"]
    auth = ("WS_GOLDENSAT", "OVERHAUL.2025")
    for documento in documentos:
        url = f"https://trafegus.over-haul.com/ws_rest/public/api/ultima-posicao-viagem?Documento={documento}"
        try:
            response = requests.get(url, auth=auth, timeout=30)
            response.raise_for_status()
            data = response.json()
            for viagem in data.get("viagem", []):
                posicao = viagem.get("posicoesViagem", {})
                if not posicao:
                    continue
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
                    continue
                # Associação da empresa pelo documento
                if documento == "61064929000179":
                    empresa = "Corteva"
                elif documento == "24315867000102":
                    empresa = "Comandolog"
                else:
                    empresa = "Desconhecida"
                trafegus_data.append({
                    "latitude": lat,
                    "longitude": lng,
                    "detalhes": {
                        "placa": posicao.get("placa"),
                        "placaCarreta": posicao.get("placaCarreta"),
                        "motorista": posicao.get("motorista"),
                        "statusCarga": posicao.get("statusCarga"),
                        "descricaoLocal": posicao.get("descricaoLocal"),
                        "dataPosicao": posicao.get("dataPosicao"),
                        "contatoMotorista": posicao.get("contatoMotorista", []),
                        "notasFiscais": posicao.get("notasFiscais", []),
                        "documento": documento,
                        "empresa": empresa
                    }
                })
        except requests.RequestException as e:
            print(f"Erro ao buscar dados para documento {documento}: {str(e)}")
            continue

    # 🚧 Cercas geográficas (mantendo todas as que você criou)
    user = request.user
    geofences = [
        {
            "name": g.geofence.nome,
            "center": [g.geofence.latitude, g.geofence.longitude],
            "radius": g.geofence.raio
        }
        for g in UserGeofence.objects.filter(user=user)
    ]

    # Filtra apenas dispositivos realmente dentro de alguma cerca para alertas
    devices_in_geofences = []
    notified_vehicles = set()
    for device in ultima_resposta_t42 + ultima_resposta_stc + trafegus_data:
        if 'latitude' in device and 'longitude' in device:
            lat = float(device['latitude']) if device['latitude'] not in [None, '', 0, '0'] else None
            lon = float(device['longitude']) if device['longitude'] not in [None, '', 0, '0'] else None
            if lat is None or lon is None:
                continue
            for geofence in geofences:
                if check_geofence(lat, lon, geofence):
                    device['current_geofence'] = geofence['name']
                    # Só notifica uma vez por device por request
                    if device.get('device_id') or device.get('placa') or (device.get('detalhes') and device['detalhes'].get('placa')):
                        unique_id = device.get('device_id') or device.get('placa') or (device.get('detalhes', {}).get('placa'))
                        if (unique_id, geofence['name']) not in notified_vehicles:
                            notify_geofence_event(device, geofence['name'])
                            notified_vehicles.add((unique_id, geofence['name']))
                    devices_in_geofences.append(device)
                    break  # Só adiciona uma vez por cerca

    response = JsonResponse({
        "t42_devices": ultima_resposta_t42,
        "stc_devices": ultima_resposta_stc,
        "trafegus_devices": trafegus_data,
        "geofences": geofences,
        "devices_in_geofences": devices_in_geofences,
        "last_update": {
            "t42": {
                "updated": t42_updated,
                "devices_count": len(ultima_resposta_t42)
            },
            "stc": {
                "updated": stc_updated,
                "devices_count": len(ultima_resposta_stc)
            },
            "trafegus": {
                "updated": True,
                "devices_count": len(trafegus_data)
            }
        },
        "stc_debug": stc_debug_info
    })
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


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

    status_carga = vehicle_data.get('statusCarga', '').upper()
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

    # Só notifica se entrou em uma nova cerca (ou saiu e entrou de novo)
    last_geofence = veiculos_cache.get(vehicle_id, {}).get('geofence')
    if current_geofence and last_geofence != current_geofence:
        notify_geofence_event(vehicle_data, current_geofence)
        vehicle_data['current_geofence'] = current_geofence
    # Notifica saída de cerca
    if last_geofence and not current_geofence:
        notify_geofence_exit_event(vehicle_data, last_geofence)
        vehicle_data['current_geofence'] = None

    # Atualiza o cache
    veiculos_cache[vehicle_id] = {
        'position': current_position,
        'geofence': current_geofence,
        'last_update': datetime.now(),
        'status': status_carga
    }
