from django.db import models
from accounts.models import Accounts


class Orders(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    SETTLEMENT_STATUS_CHOICES = [
        ('pending', 'Pending Bank Transfer'),
        ('processed', 'Processed'),
    ]
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, default='')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    settlement_status = models.CharField(max_length=20, choices=SETTLEMENT_STATUS_CHOICES, default='pending')
    settled_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f'Order #{self.id} - {self.user.name}'
