from django.shortcuts import render, get_object_or_404
from django.conf import settings
import math
from products.models import Products
from accounts.models import Producers, Accounts


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
            'image': product.image.url if product.image else None,
            'is_surplus': product.is_surplus,
            'surplus_price': str(product.surplus_price) if product.surplus_price else None,
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
    search_query = request.GET.get('Search', '')
    
    # Fetch products from database
    if category:
        products = Products.objects.filter(category=category, is_available=True)
    else:
        products = Products.objects.filter(is_available=True)
    
    # Convert products to display format
    product_list = []
    def _product_dict(product):
        return {
            'id': product.id,
            'name': product.name,
            'farm': product.producer.business_name if product.producer else 'Unknown',
            'price': str(product.price),
            'category': product.category,
            'image': product.image.url if product.image else None,
            'is_organic': product.is_organic if "Organic Certified" else None,
            'allergens': product.allergens,
            'is_surplus': product.is_surplus,
            'surplus_price': str(product.surplus_price) if product.surplus_price else None,
            'best_before': product.best_before,
        }

    if search_query:
        for product in products:
            if search_query.lower() in product.name.lower():
                product_list.append({
                    'id': product.id,
                    'name': product.name,
                    'farm': product.producer.business_name if product.producer else 'Unknown',
                    'price': str(product.price),
                    'category': product.category,
                    'image': product.image.url if product.image else None,
                    'is_organic': product.is_organic if "Organic Certified" else None,
                    'allergens': product.allergens,
                })
    else:
        product_list = [_product_dict(p) for p in products]


    return render(request, 'home/shop.html', {
        'products': product_list,
        'selected_category': category,
        'search': search_query,
    })


def product_detail(request, product_id):
    """Product detail page with full description, allergens, and producer info."""
    product = get_object_or_404(Products, id=product_id)
    producer = product.producer

    # Calculate distance
    distance = None
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    if producer.latitude and producer.longitude:
        ref_lat, ref_lng = 51.4545, -2.5879
        if user_id and user_type == 'customer':
            customer = Accounts.objects.filter(id=user_id).first()
            if customer and customer.latitude and customer.longitude:
                ref_lat, ref_lng = customer.latitude, customer.longitude
        distance = round(_haversine(ref_lat, ref_lng, producer.latitude, producer.longitude), 1)

    return render(request, 'home/product_detail.html', {
        'product': product,
        'producer': producer,
        'distance': distance,
    })


def producers(request):
    """Producers page with map and food miles calculation."""
    category = request.GET.get('category', '')

    if category:
        all_producers = Producers.objects.filter(products__category=category, is_active=True).distinct()
    else:
        all_producers = Producers.objects.filter(is_active=True)

    # Get customer location for food miles calculation
    customer_lat = None
    customer_lng = None
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if user_id and user_type == 'customer':
        customer = Accounts.objects.filter(id=user_id).first()
        if customer:
            customer_lat = getattr(customer, 'latitude', None)
            customer_lng = getattr(customer, 'longitude', None)

    # Bristol city centre as default centre point
    default_lat = 51.4545
    default_lng = -2.5879

    producer_list = []
    for producer in all_producers:
        p_lat = producer.latitude
        p_lng = producer.longitude

        # Calculate food miles if both locations available
        distance = None
        if p_lat and p_lng and customer_lat and customer_lng:
            distance = _haversine(customer_lat, customer_lng, p_lat, p_lng)
        elif p_lat and p_lng:
            distance = _haversine(default_lat, default_lng, p_lat, p_lng)

        producer_list.append({
            'id': producer.id,
            'name': producer.business_name,
            'description': producer.description,
            'address': producer.address,
            'postal_code': producer.postal_code,
            'latitude': p_lat,
            'longitude': p_lng,
            'distance': round(distance, 1) if distance is not None else None,
            'collection_available': producer.collection_available,
            'delivery_available': producer.delivery_available,
            'image_url': producer.business_image.url if producer.business_image else None,
        })

    # Sort by distance if available
    producer_list.sort(key=lambda p: p['distance'] if p['distance'] is not None else 9999)

    return render(request, 'home/producers.html', {
        'producers': producer_list,
        'selected_category': category,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'default_lat': default_lat,
        'default_lng': default_lng,
    })


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance in miles between two GPS coordinate pairs."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def store(request, producer_id):
    """Public store page for a producer."""
    producer = get_object_or_404(Producers, id=producer_id, is_active=True)
    products = Products.objects.filter(producer=producer, is_available=True)

    # Calculate distance from customer or Bristol centre
    distance = None
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    if producer.latitude and producer.longitude:
        ref_lat, ref_lng = 51.4545, -2.5879
        if user_id and user_type == 'customer':
            customer = Accounts.objects.filter(id=user_id).first()
            if customer and customer.latitude and customer.longitude:
                ref_lat, ref_lng = customer.latitude, customer.longitude
        distance = round(_haversine(ref_lat, ref_lng, producer.latitude, producer.longitude), 1)

    return render(request, 'home/store.html', {
        'producer': producer,
        'products': products,
        'distance': distance,
    })
