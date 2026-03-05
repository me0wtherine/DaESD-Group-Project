from django import forms
from .models import Accounts, Producers


class SignupForm(forms.ModelForm):
    """Customer registration form."""

    class Meta:
        model = Accounts
        fields = ['name', 'email', 'phone_number', 'password']
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
