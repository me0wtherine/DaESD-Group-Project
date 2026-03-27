from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('confirm/', views.payment_page, name='payment_page'),
    path('create-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
