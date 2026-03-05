from django.db import models
from accounts.models import Producers
from orders.models import Orders


class WeeklyPayment(models.Model):
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    account_number = models.CharField(max_length=20, blank=True, default='')
    account_name = models.CharField(max_length=100, blank=True, default='')
    sort_code = models.CharField(max_length=10, blank=True, default='')

    def __str__(self):
        return f'WeeklyPayment #{self.id}'


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
