from django.db import models

# Create your models here.
class Cart(models.Model):
    CartID
    UserID

class CartItem(models.Model):
    ProdID
    Quantity
    CartID
    