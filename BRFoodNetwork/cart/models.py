from django.db import models
from accounts.models import Accounts
from products.models import Products


class Cart(models.Model):
    user = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='carts')

    def __str__(self):
        return f'Cart #{self.id} - {self.user.name}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'
    