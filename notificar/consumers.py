from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import AlertLog
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        self.user = self.scope["user"]
        self.room_group_name = f"notifications_{self.user.id}"
        self.general_group_name = "notifications"  # Grupo geral para notificações

        # Entra no grupo de notificações do usuário
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Entra no grupo geral de notificações
        await self.channel_layer.group_add(
            self.general_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Sai dos grupos de notificações
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.general_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')

        if message == 'get_unread_count':
            count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'unread_count': count
            }))

    async def notification_message(self, event):
        # Envia a notificação para o WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))

    @database_sync_to_async
    def get_unread_count(self):
        return AlertLog.objects.filter(notified=False).exclude(user=self.user).count()

    def parse_stc_data(self, stc_raw_data):
        if isinstance(stc_raw_data, dict) and stc_raw_data.get("success") and "data" in stc_raw_data:
            pass
        else:
            print("⚠️ API STC retornou formato inválido.")

        content_type = stc_raw_data.headers.get('content-type', '').lower()
        if stc_raw_data.status_code == 200 and 'application/json' in content_type:
            pass
        else:
            print(f"⚠️ API STC falhou com status {stc_raw_data.status_code} ou tipo de conteúdo inválido ({content_type}).")

        if stc_raw_data.status_code == 200 and 'application/json' in content_type:
            pass
        else:
            return JsonResponse({"error": "A API STC não retornou JSON válido", "stc_debug": stc_raw_data.text[:1000]}, status=502) 