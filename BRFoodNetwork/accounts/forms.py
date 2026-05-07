from django import forms
from .models import Accounts, Producers, Admins


class SignupForm(forms.ModelForm):
    """Customer registration form."""
    password  = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm password")

    class Meta:
        model = Accounts
        fields = ['name', 'email', 'phone_number', 'address', 'postal_code','customer_type', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
        fields = ['name', 'email', 'phone_number', 'address', 'postal_code', 'password']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


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
