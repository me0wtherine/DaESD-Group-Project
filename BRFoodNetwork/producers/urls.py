from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='producer_dashboard'),
    path('products/', views.producer_products, name='producer_products'),
    path('orders/', views.producer_orders, name='producer_orders'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('surplus-deals/', views.surplus_deals, name='surplus_deals'),
    path('payouts/', views.producer_payouts, name='producer_payouts'),
    path('update-store/', views.update_store, name='update_store'),
    path('edit-store/', views.edit_store, name='edit_store'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('settlements/', views.weekly_settlements, name='weekly_settlements'),
    
    # Recipe management routes
    path('recipes/', views.recipes_list, name='recipes_list'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path('recipes/<int:recipe_id>/edit/', views.edit_recipe, name='edit_recipe'),
    path('recipes/<int:recipe_id>/delete/', views.delete_recipe, name='delete_recipe'),
]
