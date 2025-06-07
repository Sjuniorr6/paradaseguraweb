import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import AlertLog
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.core.paginator import Paginator
from django.utils import timezone
import pytz

@login_required
def log_button_click(request):
    if request.method == 'POST':
        btn = request.POST.get('button')
        # Cria o log com notified=False por padrão
        alert = AlertLog.objects.create(user=request.user, button=btn)
        
        # Envia notificação para todos os usuários exceto o que criou o alerta
        channel_layer = get_channel_layer()
        for user in alert.user.__class__.objects.exclude(id=request.user.id):
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user.id}",
                {
                    "type": "notification_message",
                    "message": {
                        "id": alert.pk,
                        "user": alert.user.username,
                        "button": alert.button,
                        "when": alert.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                }
            )
        
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'POST only'}, status=400)

@login_required
def pending_alerts(request):
    """
    GET /notificar/ajax/pending-alerts/?since=ISO_TIMESTAMP
    Retorna só os AlertLog que ainda não foram notificados (notified=False),
    com timestamp > since, **exceto** os criados pelo próprio usuário.
    Depois marca como notificado.
    """
    since = request.GET.get('since')

    # 1) Pega apenas os não-notificados e exclui os do usuário atual
    qs = AlertLog.objects.filter(notified=False) \
                         .exclude(user=request.user) \
                         .order_by('timestamp')

    # 2) Filtra por timestamp se fornecido
    if since:
        try:
            dt = datetime.datetime.fromisoformat(since)
            qs = qs.filter(timestamp__gt=dt)
        except ValueError:
            pass

    # 3) Prepara o JSON de saída e acumula os IDs para marcar
    alerts = []
    ids_to_mark = []
    for a in qs:
        alerts.append({
            'id':     a.pk,
            'user':   a.user.username,
            'button': a.button,
            'when':   a.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
        })
        ids_to_mark.append(a.pk)

    # 4) Marca todos esses logs como notificados
    if ids_to_mark:
        AlertLog.objects.filter(pk__in=ids_to_mark).update(notified=True)

    return JsonResponse({'alerts': alerts})

from django.shortcuts import render
from .models import AlertLog

def alertlog_list(request):
    logs = AlertLog.objects.filter(alert_type='button').order_by('-timestamp')
    paginator = Paginator(logs, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Ajusta o horário para America/Sao_Paulo
    tz = pytz.timezone('America/Sao_Paulo')
    for log in page_obj:
        if log.timestamp:
            log.timestamp_sp = timezone.localtime(log.timestamp, tz)
        else:
            log.timestamp_sp = None
    return render(request, 'alertlog_list.html', {'page_obj': page_obj})
