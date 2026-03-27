from django.contrib import admin
from .models import Orders, OrderItem


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order_status', 'total_price', 'order_date', 'settlement_status']
    list_filter = ['order_status', 'settlement_status', 'fulfillment_type']
    search_fields = ['user__name', 'user__email']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['product__name']
