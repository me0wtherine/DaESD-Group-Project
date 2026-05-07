from django import forms
from .models import Accounts, Producers, Admins


class SignupForm(forms.ModelForm):
    """Customer registration form."""

    class Meta:
        model = Accounts
        fields = ['name', 'email', 'phone_number', 'address', 'postal_code','customer_type', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }


class ProducerSignupForm(forms.ModelForm):
    """Producer registration form."""

    class Meta:
        model = Producers
        fields = ['business_name', 'email', 'phone_number', 'address', 'postal_code', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }


class CustomerLoginForm(forms.Form):
    """Customer log-in form."""
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


class ProducerLoginForm(forms.Form):
    """Producer log-in form."""
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

class AdminSignupForm(forms.ModelForm):
    """Admin account creation form."""

    class Meta:
        model = Admins 
        fields = ['name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class AdminLoginForm(forms.Form):
    """Admin log-in form."""
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
