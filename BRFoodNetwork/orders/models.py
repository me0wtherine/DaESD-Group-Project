from django.db import models

# Create your models here.
class Orders(models.Model):
    OrderID
    Order_Date
    Delivery_Date
    UserID
    Payment_Method
    Order_Status
    Total_Price
