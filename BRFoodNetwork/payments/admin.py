from django.contrib import admin
from .models import Payments, WeeklyPayment


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'producer', 'producer_payment', 'network_commission']
    list_filter = ['producer']
    search_fields = ['order__user__name', 'producer__business_name']


@admin.register(WeeklyPayment)
class WeeklyPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'producer', 'week_starting', 'total_payment', 'total_commission']
    list_filter = ['week_starting', 'producer']
