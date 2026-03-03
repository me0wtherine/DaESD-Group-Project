from django.shortcuts import render, redirect
from .forms import SignupForm
from .forms import ProducerSignupForm

# Create your views here.

def SignUpView(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = SignupForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def ProducerSignUpView(request):
    if request.method == 'POST':
        form = ProducerSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProducerSignupForm()
    
    return render(request, 'registration/producersignup.html', {'form': form})
