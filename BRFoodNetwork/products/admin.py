from django.contrib import admin

from .models import Products


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    """Admin view for product listings."""
    list_display = ['name', 'producer', 'category', 'price', 'is_available']
    list_filter = ['category', 'is_available', 'is_organic']
    search_fields = ['name', 'producer__business_name']
