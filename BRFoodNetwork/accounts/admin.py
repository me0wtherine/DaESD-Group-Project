from django.contrib import admin
from .models import Accounts, Producers

# Register your models here.

@admin.register(Accounts)
class AccountsAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number']
    search_fields = ['name', 'email']

@admin.register(Producers)
class ProducersAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone_number']
    search_fields = ['business_name', 'email']
