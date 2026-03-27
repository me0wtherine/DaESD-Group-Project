from django.db import models
from django.utils import timezone
from accounts.models import Producers
from orders.models import Orders


class WeeklyPayment(models.Model):
    producer = models.ForeignKey(Producers, on_delete=models.CASCADE, related_name='weekly_payments', null=True, blank=True)
    week_starting = models.DateField(null=True, blank=True)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    account_number = models.CharField(max_length=20, blank=True, default='')
    account_name = models.CharField(max_length=100, blank=True, default='')
    sort_code = models.CharField(max_length=10, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'WeeklyPayment #{self.id} - {self.producer.business_name if self.producer else "N/A"}'


class Payments(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='payments')
    network_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    producer_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    producer = models.ForeignKey(Producers, on_delete=models.CASCADE, related_name='payments')
    weekly_payment = models.ForeignKey(WeeklyPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    class Meta:
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f'Payment #{self.id} for Order #{self.order.id}'
