from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='producer_dashboard'),
    path('update-store/', views.update_store, name='update_store'),
    path('edit-store/', views.edit_store, name='edit_store'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]
