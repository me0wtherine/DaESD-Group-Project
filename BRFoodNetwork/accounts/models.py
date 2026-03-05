from django.db import models

# Create your models here.
class Accounts(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
class Producers(models.Model): 
    business_name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    store_description = models.TextField(blank=True, default='', max_length=2000)
    business_image = models.ImageField(upload_to='producer_images/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='producer_banners/', blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)
    collection_available = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)
    opening_hours = models.JSONField(blank=True, default=dict)
    certifications = models.TextField(blank=True, default='')
    farm_story = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.business_name

#class Restaurant(models.Model): RestaurantName
#class Communities(models.Model): CommunityName, Status, Inst_email
#class Individuals(models.Model): 