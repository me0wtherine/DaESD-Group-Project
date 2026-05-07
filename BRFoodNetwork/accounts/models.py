from django.db import models


class Accounts(models.Model):
    """Customer accounts for the food network."""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=20)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    CUSTOMER_TYPE_CHOICES = {
        ("individual", "Individual"),
        ("restaurant", "Restaurant"),
        ("community_group", "Community Group"),
    }

    customer_type = models.CharField(
        max_length=30,
        choices=CUSTOMER_TYPE_CHOICES,
        default="individual"

    )

    class Meta:
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.name


class Producers(models.Model):
    """Producer/farm accounts that list products on the network."""
    business_name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, help_text='Short tagline for your business')
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
    latitude = models.FloatField(null=True, blank=True, help_text='GPS latitude for map pin')
    longitude = models.FloatField(null=True, blank=True, help_text='GPS longitude for map pin')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Producers'

    def __str__(self):
        return self.business_name
    
class Admins(models.Model): 
    """Admin accounts for managing the network."""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Admins'

    def __str__(self):
        return self.name


#class Restaurant(models.Model): RestaurantName
#class Communities(models.Model): CommunityName, Status, Inst_email

