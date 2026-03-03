from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .forms import SignupForm, ProducerSignupForm, CustomerLoginForm, ProducerLoginForm
from .models import Accounts, Producers

# Create your views here.

def account_type_signup(request):
    return render(request, 'registration/account_type_signup.html')

def account_type_login(request):
    return render(request, 'registration/account_type_login.html')

def SignUpView(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            # Hash the password before saving
            account.password = make_password(form.cleaned_data['password'])
            account.save()
            messages.success(request, 'Account created successfully!')
            return redirect('customer_login')
    else:
        form = SignupForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def ProducerSignUpView(request):
    if request.method == 'POST':
        form = ProducerSignupForm(request.POST)
        if form.is_valid():
            producer = form.save(commit=False)
            # Hash the password before saving
            producer.password = make_password(form.cleaned_data['password'])
            producer.save()
            messages.success(request, 'Producer account created successfully!')
            return redirect('producer_login')
    else:
        form = ProducerSignupForm()
    
    return render(request, 'registration/producersignup.html', {'form': form})

def customer_login(request):
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = Accounts.objects.get(email=email)
                # Verify hashed password
                if check_password(password, user.password):
                    # Store user_id in session
                    request.session['user_id'] = user.id
                    request.session['user_type'] = 'customer'
                    messages.success(request, f'Welcome back, {user.name}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid email or password')
            except Accounts.DoesNotExist:
                messages.error(request, 'Invalid email or password')
    else:
        form = CustomerLoginForm()
    
    return render(request, 'registration/customer_login.html', {'form': form})

def producer_login(request):
    if request.method == 'POST':
        form = ProducerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                producer = Producers.objects.get(email=email)
                # Verify hashed password
                if check_password(password, producer.password):
                    # Store producer_id in session
                    request.session['user_id'] = producer.id
                    request.session['user_type'] = 'producer'
                    messages.success(request, f'Welcome back, {producer.business_name}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid email or password')
            except Producers.DoesNotExist:
                messages.error(request, 'Invalid email or password')
    else:
        form = ProducerLoginForm()
    
    return render(request, 'registration/producer_login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')
