from django.db import models

# Create your models here.
class Member(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
#class Producers(models.Model): BusinessName, Description
#class Restaurant(models.Model): RestaurantName
#class Communities(models.Model): CommunityName, Status, Inst_email
#class Individuals(models.Model): 