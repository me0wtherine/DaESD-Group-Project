from django import forms
from accounts.models import Producers
from products.models import Products, Recipe
from django.forms import CheckboxSelectMultiple


ALLERGEN_CHOICES = [
    ('celery', 'Celery'),
    ('gluten', 'Gluten'),
    ('lupin', 'Lupin'),
    ('crustaceans', 'Crustaceans'),
    ('milk', 'Milk'),
    ('sulphur_dioxide', 'Sulphur Dioxide'),
    ('sesame', 'Sesame'),
    ('molluscs', 'Molluscs'),
    ('mustard', 'Mustard'),
    ('nuts', 'Nuts'),
    ('egg', 'Egg'),
    ('fish', 'Fish'),
    ('soybeans', 'Soybeans'),
    ('peanuts', 'Peanuts'),
]

class StoreInfoForm(forms.ModelForm):
    """Form for producers to edit their store details"""
    class Meta:
        model = Producers
        fields = ['business_name', 'store_description', 'business_image', 'address', 'phone_number', 'postal_code']
        widgets = {
            'business_name': forms.TextInput(attrs={'placeholder': 'Your business name'}),
            'store_description': forms.Textarea(attrs={
                'placeholder': 'Tell customers about your business, what you grow/produce, your story...',
                'rows': 5,
            }),
            'address': forms.TextInput(attrs={'placeholder': 'Business address'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Contact number'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal code'}),
        }
        labels = {
            'business_name': 'Business Name',
            'store_description': 'Store Description',
            'business_image': 'Business Picture',
            'address': 'Address',
            'phone_number': 'Phone Number',
            'postal_code': 'Postal Code',
        }


class ProductForm(forms.ModelForm):
    """Form for producers to add/edit products"""
    class Meta:
        model = Products
        fields = ['name', 'category', 'description', 'price', 'unit', 'stock_quantity',
                  'is_available', 'is_organic', 'allergens', 'image',
                  'available_from', 'available_to']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Product name'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe your product...',
                'rows': 3,
            }),
            'price': forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'unit': forms.TextInput(attrs={'placeholder': 'e.g. per kg, per bunch, each'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0'}),
            'allergens': CheckboxSelectMultiple(choices=ALLERGEN_CHOICES),
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'description': 'Description',
            'price': 'Price (£)',
            'unit': 'Unit',
            'stock_quantity': 'Stock Quantity',
            'is_available': 'Available for sale',
            'is_organic': 'Organic certified',
            'allergens': 'Allergens',
            'image': 'Product Image',
            'available_from': 'Available From',
            'available_to': 'Available To',
        }


class RecipeForm(forms.ModelForm):
    """Form for producers to add/edit recipes"""
    products = forms.ModelMultipleChoiceField(
        queryset=Products.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Select products used in this recipe'
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'image', 
                  'products', 'season', 'prep_time_minutes', 'cook_time_minutes', 'serves', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Recipe title',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Share the story behind this recipe and why customers should try it...',
                'rows': 3,
                'class': 'form-control'
            }),
            'ingredients': forms.Textarea(attrs={
                'placeholder': 'List ingredients, one per line',
                'rows': 5,
                'class': 'form-control'
            }),
            'instructions': forms.Textarea(attrs={
                'placeholder': 'Step-by-step cooking instructions',
                'rows': 6,
                'class': 'form-control'
            }),
            'season': forms.Select(attrs={'class': 'form-control'}),
            'prep_time_minutes': forms.NumberInput(attrs={
                'placeholder': 'Preparation time (minutes)',
                'min': '0',
                'class': 'form-control'
            }),
            'cook_time_minutes': forms.NumberInput(attrs={
                'placeholder': 'Cooking time (minutes)',
                'min': '0',
                'class': 'form-control'
            }),
            'serves': forms.TextInput(attrs={
                'placeholder': 'e.g. Serves 4, Makes 12 cookies',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Recipe Title',
            'description': 'Recipe Story',
            'ingredients': 'Ingredients',
            'instructions': 'Cooking Instructions',
            'image': 'Recipe Image',
            'products': 'Linked Products',
            'season': 'Season (Optional)',
            'prep_time_minutes': 'Prep Time (minutes)',
            'cook_time_minutes': 'Cook Time (minutes)',
            'serves': 'Serving Size',
            'is_published': 'Publish Recipe',
        }

    def __init__(self, *args, producer=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter products to only show the producer's products
        if producer:
            self.fields['products'].queryset = Products.objects.filter(producer=producer)
        else:
            self.fields['products'].queryset = Products.objects.none()
