import json
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.models import Producers
from products.models import Products
from .forms import StoreInfoForm, ProductForm

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def producer_required(view_func):
    """Decorator to ensure only logged-in producers can access the view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_type') != 'producer' or 'user_id' not in request.session:
            messages.error(request, 'You must be logged in as a producer to access this page.')
            return redirect('producer_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_opening_hours_list(producer):
    """Convert the stored opening_hours JSON into a list of dicts for the template."""
    hours = producer.opening_hours
    if isinstance(hours, list):
        return hours
    return []


@producer_required
def dashboard(request):
    """Main producer dashboard / manage store page"""
    producer = get_object_or_404(Producers, id=request.session['user_id'])
    products = Products.objects.filter(producer=producer)
    opening_hours = _get_opening_hours_list(producer)

    return render(request, 'producers/dashboard.html', {
        'producer': producer,
        'products': products,
        'opening_hours': opening_hours,
        'weekdays': WEEKDAYS,
        'weekdays_json': json.dumps(WEEKDAYS),
    })


@producer_required
def update_store(request):
    """Handle the big save-all form on the manage store page."""
    producer = get_object_or_404(Producers, id=request.session['user_id'])

    if request.method == 'POST':
        # Text fields
        producer.store_description = request.POST.get('store_description', '')
        producer.phone_number = request.POST.get('phone_number', '')
        producer.email = request.POST.get('email', producer.email)
        producer.address = request.POST.get('address', '')
        producer.collection_available = 'collection_available' in request.POST
        producer.delivery_available = 'delivery_available' in request.POST
        producer.certifications = request.POST.get('certifications', '')
        producer.farm_story = request.POST.get('farm_story', '')

        # Images
        if 'business_image' in request.FILES:
            producer.business_image = request.FILES['business_image']
        if 'banner_image' in request.FILES:
            producer.banner_image = request.FILES['banner_image']

        # Opening hours
        days = request.POST.getlist('oh_day')
        opens = request.POST.getlist('oh_open')
        closes = request.POST.getlist('oh_close')
        opening_hours = []
        for d, o, c in zip(days, opens, closes):
            if d and (o or c):
                opening_hours.append({'day': d, 'open': o, 'close': c})
        producer.opening_hours = opening_hours

        producer.save()
        messages.success(request, 'Store information saved successfully!')
    return redirect('producer_dashboard')


@producer_required
def edit_store(request):
    """Edit store information, description, and business picture"""
    producer = get_object_or_404(Producers, id=request.session['user_id'])

    if request.method == 'POST':
        form = StoreInfoForm(request.POST, request.FILES, instance=producer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store information updated successfully!')
            return redirect('producer_dashboard')
    else:
        form = StoreInfoForm(instance=producer)

    return render(request, 'producers/edit_store.html', {
        'form': form,
        'producer': producer,
    })


@producer_required
def add_product(request):
    """Add a new product listing"""
    producer = get_object_or_404(Producers, id=request.session['user_id'])

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = producer
            product.save()
            messages.success(request, f'"{product.name}" has been listed successfully!')
            return redirect('producer_dashboard')
    else:
        form = ProductForm()

    return render(request, 'producers/add_product.html', {
        'form': form,
        'producer': producer,
    })


@producer_required
def edit_product(request, product_id):
    """Edit an existing product"""
    producer = get_object_or_404(Producers, id=request.session['user_id'])
    product = get_object_or_404(Products, id=product_id, producer=producer)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" has been updated!')
            return redirect('producer_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'producers/edit_product.html', {
        'form': form,
        'producer': producer,
        'product': product,
    })


@producer_required
def delete_product(request, product_id):
    """Delete a product listing"""
    producer = get_object_or_404(Producers, id=request.session['user_id'])
    product = get_object_or_404(Products, id=product_id, producer=producer)

    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" has been removed.')
    return redirect('producer_dashboard')
