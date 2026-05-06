from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
]
