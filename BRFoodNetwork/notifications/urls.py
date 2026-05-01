from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('notifications/', views.notifications, name='notifications'),
]
