from django.db import models

# Create your models here.
class Products(models.Model):
    ProdID = models.CharField(max_length=100)
    Prod_Name
    ProducerID
    Category
    Description
    Organic_Certification
    Price
    Unit
    Availability
    Stock_Quantity
    Allergens
    Harvest_Date
    Prod_Img
