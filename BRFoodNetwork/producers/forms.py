from django import forms
from accounts.models import Producers
from products.models import Products


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
            'allergens': forms.TextInput(attrs={'placeholder': 'e.g. nuts, gluten, dairy'}),
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'is_available': 'Available for sale',
            'is_organic': 'Organic certified',
            'available_from': 'Available From',
            'available_to': 'Available To',
        }
