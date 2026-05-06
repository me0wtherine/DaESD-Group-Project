from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

from .forms import AdminSignupForm, AdminLoginForm, SignupForm, ProducerSignupForm, CustomerLoginForm, ProducerLoginForm
from .models import Accounts, Producers, Admins
from .geocoding import geocode_address, is_within_bristol_radius
from orders.models import Orders
from cart.models import Cart, CartItem

def account_type_signup(request):
    """Choose between customer or producer sign-up."""
    return render(request, 'registration/account_type_signup.html')


def account_type_login(request):
    """Choose between customer or producer log-in."""
    return render(request, 'registration/account_type_login.html')


def signup_view(request):
    """Customer account registration."""
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.password = make_password(form.cleaned_data['password'])

            # Geocode address and enforce 20-mile radius
            lat, lng = geocode_address(account.address, account.postal_code)
            if lat is None or lng is None:
                messages.error(request, 'We could not verify your address. Please enter a valid UK address and postal code.')
                return render(request, 'registration/signup.html', {'form': form})

            if not is_within_bristol_radius(lat, lng):
                messages.error(request, 'Sorry, the Bristol Regional Food Network only serves customers within a 20-mile radius of Bristol city centre.')
                return render(request, 'registration/signup.html', {'form': form})

            account.latitude = lat
            account.longitude = lng
            account.save()
            messages.success(request, 'Account created successfully!')
            return redirect('customer_login')
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


def producer_signup_view(request):
    """Producer account registration."""
    if request.method == 'POST':
        form = ProducerSignupForm(request.POST)
        if form.is_valid():
            producer = form.save(commit=False)
            producer.password = make_password(form.cleaned_data['password'])

            # Geocode address for map pin and enforce 20-mile radius
            lat, lng = geocode_address(producer.address, producer.postal_code)
            if lat is None or lng is None:
                messages.error(request, 'We could not verify your address. Please enter a valid UK address and postal code.')
                return render(request, 'registration/producersignup.html', {'form': form})

            if not is_within_bristol_radius(lat, lng):
                messages.error(request, 'Sorry, the Bristol Regional Food Network only accepts producers within a 20-mile radius of Bristol city centre.')
                return render(request, 'registration/producersignup.html', {'form': form})

            producer.latitude = lat
            producer.longitude = lng
            producer.save()
            messages.success(request, 'Producer account created successfully!')
            return redirect('producer_login')
    else:
        form = ProducerSignupForm()

    return render(request, 'registration/producersignup.html', {'form': form})


def customer_login(request):
    """Customer log-in with email and password."""
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = Accounts.objects.get(email=email)
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['user_type'] = 'customer'
                    request.session['user_name'] = user.name
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
    """Producer log-in with email and password."""
    if request.method == 'POST':
        form = ProducerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                producer = Producers.objects.get(email=email)
                if check_password(password, producer.password):
                    request.session['user_id'] = producer.id
                    request.session['user_type'] = 'producer'
                    request.session['user_name'] = producer.business_name
                    messages.success(request, f'Welcome back, {producer.business_name}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid email or password')
            except Producers.DoesNotExist:
                messages.error(request, 'Invalid email or password')
    else:
        form = ProducerLoginForm()

    return render(request, 'registration/producer_login.html', {'form': form})


def order_history(request):
    """Show logged-in customers their past orders."""
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'customer':
        messages.error(request, 'You must be logged in as a customer to view your order history.')
        return redirect('customer_login')

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        request.session.flush()
        messages.error(request, 'Please log in again.')
        return redirect('customer_login')

    orders = Orders.objects.filter(user=customer).order_by('-order_date')

    return render(request, 'accounts/order_history.html', {
        'customer': customer,
        'orders': orders,
    })

def reorder(request, order_id):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type != 'customer':
        messages.error(request, 'You must be logged in as a customer to reorder.')
        return redirect('customer_login')
    
    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        request.session.flush()
        return redirect('customer_login')
    order = get_object_or_404(Orders, id=order_id, user=customer)

    cart, _ = Cart.objects.get_or_create(user=customer)

    for item in order.items.all():
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=item.product,
            defaults={'quantity': item.quantity}

        )

        if not created:
            cart_item.quantity += item.quantity
            cart_item.save()
        
        messages.success(request, 'Items from this order have been added to your basket.')
        return redirect('cart:detail')


def logout_view(request):
    """Clear the session and redirect to the homepage."""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')

def admin_home(request):
    """Admin dashboard showing all producers and their statuses."""
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    user_name = request.session.get('user_name')

    if not user_id or user_type != 'admin':
        messages.error(request, 'You must be logged in as an admin to access the admin dashboard.')
        return redirect('account_type_login')

    producers = Producers.objects.all()

    return render(request, 'admin/admin_home.html', {
        'user_name': user_name,
        'producers': producers,
    })

def create_admin_account(request):
    """Utility function to create an admin account."""
    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            admin = form.save(commit=False)
            admin.password = make_password(form.cleaned_data['password'])
            admin.save()
            messages.success(request, 'Admin account created successfully!')
            return redirect('admin_dashboard')
    else:
        form = AdminSignupForm()

    return render(request, 'admin/admin_account_create.html', {'form': form})
    
def admin_login(request):
    """Admin log-in with email and password."""
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                admin = Admins.objects.get(email=email)
                if check_password(password, admin.password):
                    request.session['user_id'] = admin.id
                    request.session['user_type'] = 'admin'
                    request.session['user_name'] = admin.name
                    messages.success(request, f'Welcome back, {admin.name}!')
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Invalid email or password')
            except Admins.DoesNotExist:
                messages.error(request, 'Invalid email or password')
    else:
        form = AdminLoginForm()

    return render(request, 'admin/admin_login.html', {'form': form})