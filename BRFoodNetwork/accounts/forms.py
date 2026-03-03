from django import forms
from .models import Accounts
from .models import Producers

class SignupForm(forms.ModelForm):
    class Meta:
        model = Accounts
        fields = ['name','email','phone_number','password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class ProducerSignupForm(forms.ModelForm):
    class Meta:
        model = Producers
        fields = ['business_name','email','phone_number','address','postal_code','password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class CustomerLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

class ProducerLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())