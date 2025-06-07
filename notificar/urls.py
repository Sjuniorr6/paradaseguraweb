from django.urls import path
from . import views

app_name = 'notificar'

urlpatterns = [
    path('ajax/log-click/', views.log_button_click,    name='log_button_click'),
    path('ajax/pending-alerts/', views.pending_alerts, name='pending_alerts'),
    path('logs/', views.alertlog_list, name='alertlog_list'),
]