from django.contrib import admin

from .models import Accounts, Producers


@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    """Admin view for customer accounts."""
    list_display = ['name', 'email', 'phone_number']
    search_fields = ['name', 'email']


@admin.register(Producers)
class ProducersAdmin(admin.ModelAdmin):
    """Admin view for producer accounts."""
    list_display = ['business_name', 'email', 'phone_number', 'is_active']
    search_fields = ['business_name', 'email']
    list_filter = ['is_active']
