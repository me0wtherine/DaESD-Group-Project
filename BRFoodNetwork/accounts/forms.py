from django import forms
from .models import Accounts, Producers, Admins
import re
from django.core.exceptions import ValidationError

def validate_strong_password(password):
    """Enforce strong password requirements."""
    errors = []

    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number.')
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        errors.append('Password must contain at least one special character.')

    if errors:
        raise ValidationError(errors)

def validate_uk_phone(phone):
    """Accept standard UK phone formats."""
    cleaned = re.sub(r'[\s\-()]', '', phone)
    if not re.match(r'^(\+44|0)(\d{10}|\d{9})$', cleaned):
        raise ValidationError(
            'Enter a valid UK phone number.'
        )

class SignupForm(forms.ModelForm):
    """Customer registration form."""
    password  = forms.CharField(widget=forms.PasswordInput(), validators=[validate_strong_password])
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm password")

    class Meta:
        model = Accounts
        fields = ['name', 'email', 'phone_number', 'address', 'postal_code']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        validate_uk_phone(phone)
        if Accounts.objects.filter(phone_number=phone).exists():
            raise ValidationError('An account with this phone number already exists.')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ProducerSignupForm(forms.ModelForm):
    """Producer registration form."""

    password  = forms.CharField(widget=forms.PasswordInput(), validators=[validate_strong_password])
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm password")

    class Meta:
        model = Producers
        fields = ['business_name', 'email', 'phone_number', 'address', 'postal_code']
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        validate_uk_phone(phone)
        if Producers.objects.filter(phone_number=phone).exists():
            raise ValidationError('An account with this phone number already exists.')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


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
    password  = forms.CharField(widget=forms.PasswordInput(), validators=[validate_strong_password])
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm password")

    class Meta:
        model = Admins 
        fields = ['name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class AdminLoginForm(forms.Form):
    """Admin log-in form."""
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
