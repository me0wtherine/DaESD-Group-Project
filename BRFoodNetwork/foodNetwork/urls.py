from django.urls import path
from foodNetwork import views

urlpatterns = [
    path("", views.home, name="home"),
    path("welcome/", views.welcome, name="welcome"),
]
