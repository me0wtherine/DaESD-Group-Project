from django import forms
from products.models import Products

class addToCart(forms.ModelForm):
    fields = ["user.id", "product.id", "quantity"]
    