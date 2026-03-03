from django import forms
from .models import Accounts
from .models import Producers

class SignupForm(forms.ModelForm):
    class Meta:
        model = Accounts
        fields = ['name','email','phone_number','address','postal_code','password']

class ProducerSignupForm(forms.ModelForm):
    class Meta:
        model = Producers
        fields = ['business_name','email','phone_number','address','postal_code','password']