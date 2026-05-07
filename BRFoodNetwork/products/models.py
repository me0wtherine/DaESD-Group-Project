from django.db import models
from accounts.models import Producers


class Products(models.Model):
    """Product listings created by producers."""

    CATEGORY_CHOICES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy'),
        ('meat', 'Meat'),
        ('bakery', 'Bakery'),
        ('preserves', 'Preserves'),
        ('seasonal_speciality', 'Seasonal Specialties'),
    ]

    producer = models.ForeignKey(Producers, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=50, default=0, help_text='e.g. per kg, per bunch, each')
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text='Producer will be alerted when stock falls below this number.',
    )
    is_available = models.BooleanField(default=True)
    is_organic = models.BooleanField(default=False)
    allergens = models.CharField(max_length=255, blank=True, default='')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    available_from = models.DateField(blank=True, null=True)
    available_to = models.DateField(blank=True, null=True)

    # Surplus deal fields
    best_before = models.DateField(blank=True, null=True, help_text='Best before / use-by date')
    is_surplus = models.BooleanField(default=False, help_text='Whether this product is on a surplus deal')
    surplus_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Discounted surplus price')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        """Average customer rating, rounded to 1 decimal. None if no reviews."""
        agg = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(agg, 1) if agg is not None else None

    @property
    def review_count(self):
        return self.reviews.count()
    
class Reviews(models.Model):
    """Customer reviews for products."""

    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey('accounts.Accounts', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Review for {self.product.name} by {self.customer.username}'


class Recipe(models.Model):
    """Recipes created by producers to share with customers."""

    SEASON_CHOICES = [
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('autumn', 'Autumn'),
        ('winter', 'Winter'),
    ]

    producer = models.ForeignKey(Producers, on_delete=models.CASCADE, related_name='recipes')
    title = models.CharField(max_length=200)
    description = models.TextField(help_text='Recipe overview and story')
    ingredients = models.TextField(help_text='List ingredients, one per line or comma-separated')
    instructions = models.TextField(help_text='Step-by-step cooking instructions')
    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True)
    products = models.ManyToManyField(Products, related_name='recipes', blank=True, help_text='Link to products used in this recipe')
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, blank=True, help_text='Seasonal tag for organization')
    prep_time_minutes = models.PositiveIntegerField(blank=True, null=True, help_text='Preparation time in minutes')
    cook_time_minutes = models.PositiveIntegerField(blank=True, null=True, help_text='Cooking time in minutes')
    serves = models.CharField(max_length=100, blank=True, help_text='Number of servings')
    is_published = models.BooleanField(default=True, help_text='Whether recipe is visible to customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.title
