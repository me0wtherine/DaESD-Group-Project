from django.shortcuts import render
from products.models import Products
from accounts.models import Producers


def home(request):
    """Homepage with popular items and nearby producers."""
    # Get category filter from query parameters
    category = request.GET.get('category', '')
    
    # Fetch products from database
    if category:
        products = Products.objects.filter(category=category, is_available=True)
    else:
        # Show popular items (top 6 most recently available products)
        products = Products.objects.filter(is_available=True).order_by('-created_at')[:6]
    
    # Convert products to display format
    popular_items = [
        {
            'id': product.id,
            'name': product.name,
            'farm': product.producer.business_name if product.producer else 'Unknown',
            'distance': 5,  # Placeholder - would need location data to calculate
            'price': str(product.price),
            'category': product.category,
        }
        for product in products
    ]
    
    # Fetch nearby producers
    nearby_producers = [
        {
            'id': producer.id,
            'name': producer.business_name,
            'distance': 5,  # Placeholder - would need location data to calculate
        }
        for producer in Producers.objects.all()[:5]
    ]

    return render(request, 'home/home.html', {
        'popular_items': popular_items,
        'nearby_producers': nearby_producers,
        'selected_category': category,
    })


def welcome(request):
    """Welcome / landing page for unauthenticated users."""
    return render(request, 'home/welcome.html')

def shop(request):
    """Shop page with product listing and filters."""
    # Get category filter from query parameters
    category = request.GET.get('category', '')
    
    # Fetch products from database
    if category:
        products = Products.objects.filter(category=category, is_available=True)
    else:
        products = Products.objects.filter(is_available=True)
    
    # Convert products to display format
    product_list = [
        {
            'id': product.id,
            'name': product.name,
            'farm': product.producer.business_name if product.producer else 'Unknown',
            'price': str(product.price),
            'category': product.category,
        }
        for product in products
    ]

    # Fetch nearby producers
    nearby_producers = [
        {
            'id': producer.id,
            'name': producer.business_name,
            'distance': 5,  # Placeholder - would need location data to calculate
        }
        for producer in Producers.objects.all()[:5]
    ]


    return render(request, 'home/shop.html', {
        'products': product_list,
        'selected_category': category,
        'nearby_producers': nearby_producers,
    })

def producers(request):
    """Producers page with producer listing and filters."""
    # Get category filter from query parameters
    category = request.GET.get('category', '')
    
    # Fetch producers from database
    if category:
        producers = Producers.objects.filter(products__category=category).distinct()
    else:
        producers = Producers.objects.all()
    
    # Convert producers to display format
    producer_list = [
        {
            'id': producer.id,
            'name': producer.business_name,
            'distance': 5,  # Placeholder - would need location data to calculate
        }
        for producer in producers
    ]

    return render(request, 'home/producers.html', {
        'producers': producer_list,
        'selected_category': category,
    })
