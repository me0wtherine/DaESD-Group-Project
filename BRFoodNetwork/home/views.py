from django.shortcuts import render, get_object_or_404
from django.conf import settings
import math
from products.models import Products, Reviews
from accounts.models import Producers, Accounts
from orders.models import Orders
from accounts.geocoding import get_driving_distance, get_driving_distances_batch


def home(request):
    """Homepage with popular items and nearby producers."""
    # Get category filter from query parameters
    category = request.GET.get('category', '')

    # Get user location for distance calculation
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    ref_lat, ref_lng = 51.4545, -2.5879  # Default to Bristol
    if user_id and user_type == 'customer':
        customer = Accounts.objects.filter(id=user_id).first()
        if customer and customer.latitude and customer.longitude:
            ref_lat, ref_lng = customer.latitude, customer.longitude

    # Fetch products from database
    if category:
        products = Products.objects.filter(category=category, is_available=True)
    else:
        products = Products.objects.filter(is_available=True).order_by('-created_at')[:6]

    # Convert products to display format
    popular_items = []
    for product in products:
        # Calculate distance from user to producer
        distance = None
        if product.producer and product.producer.latitude and product.producer.longitude:
            result = get_driving_distance(ref_lat, ref_lng, product.producer.latitude, product.producer.longitude)
            distance = round(result['distance_miles'], 1)
        
        popular_items.append({
            'id': product.id,
            'name': product.name,
            'farm': product.producer.business_name if product.producer else 'Unknown',
            'distance': distance,
            'price': str(product.price),
            'category': product.category,
            'image': product.image.url if product.image else None,
            'is_surplus': product.is_surplus,
            'surplus_price': str(product.surplus_price) if product.surplus_price else None,
        })
    
    # Fetch nearby producers
    nearby_producers = []
    for producer in Producers.objects.all()[:5]:
        distance = None
        if producer.latitude and producer.longitude:
            result = get_driving_distance(ref_lat, ref_lng, producer.latitude, producer.longitude)
            distance = round(result['distance_miles'], 1)
        
        nearby_producers.append({
            'id': producer.id,
            'name': producer.business_name,
            'distance': distance,
        })

    return render(request, 'home/home.html', {
        'popular_items': popular_items,
        'nearby_producers': nearby_producers,
        'selected_category': category,
    })


def welcome(request):
    """Welcome / landing page for unauthenticated users."""
    return render(request, 'home/welcome.html')

def shop(request):
    import ast
    """Shop page with product listing and filters."""
    # Get category filter from query parameters
    category = request.GET.get('category', '')
    search_query = request.GET.get('Search', '')
    allergens = request.GET.get('allergens', '')
    organic = request.GET.get('organic', '')
    
    # Allergen labels for display
    ALLERGEN_LABELS = {
        'celery': 'Celery', 'gluten': 'Gluten', 'lupin': 'Lupin',
        'crustaceans': 'Crustaceans', 'milk': 'Milk', 'sulphur_dioxide': 'Sulphur Dioxide',
        'sesame': 'Sesame', 'molluscs': 'Molluscs', 'mustard': 'Mustard',
        'nuts': 'Nuts', 'egg': 'Egg', 'fish': 'Fish',
        'soybeans': 'Soybeans', 'peanuts': 'Peanuts',
    }
    
    # Get user location for distance calculation
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    ref_lat, ref_lng = 51.4545, -2.5879  # Default to Bristol
    if user_id and user_type == 'customer':
        customer = Accounts.objects.filter(id=user_id).first()
        if customer and customer.latitude and customer.longitude:
            ref_lat, ref_lng = customer.latitude, customer.longitude
    
    # Fetch products from database
    products = Products.objects.filter(is_available=True)

    if category:
        products = Products.objects.filter(category=category)
    
    if allergens:
        products = products.exclude(allergens__icontains=allergens)

    if organic:
        products = products.filter(is_organic=True)

    # Convert products to display format
    product_list = []
    for product in products:
        if search_query and search_query.lower() not in product.name.lower():
            continue
        
        # Parse allergens from string representation
        allergen_display = ''
        if product.allergens:
            try:
                allergen_list = ast.literal_eval(product.allergens) if isinstance(product.allergens, str) else product.allergens
                allergen_display = ', '.join(ALLERGEN_LABELS.get(a, a) for a in allergen_list)
            except (ValueError, SyntaxError):
                allergen_display = product.allergens
        
        # Calculate distance from user to producer
        distance = None
        if product.producer.latitude and product.producer.longitude:
            result = get_driving_distance(ref_lat, ref_lng, product.producer.latitude, product.producer.longitude)
            distance = round(result['distance_miles'], 1)
        
        product_list.append({
            'id': product.id,
            'name': product.name,
            'farm': product.producer.business_name if product.producer else 'Unknown',
            'distance': distance,
            'price': str(product.price),
            'category': product.category,
            'image': product.image.url if product.image else None,
            'is_organic': product.is_organic,
            'allergens': allergen_display,
            'is_surplus': product.is_surplus,
            'surplus_price': str(product.surplus_price) if product.surplus_price else None,
            'best_before': product.best_before,
        })


    return render(request, 'home/shop.html', {
        'products': product_list,
        'selected_category': category,
        'search': search_query,
        'selected_allergens': allergens,
    })


def product_detail(request, product_id):
    import ast
    """Product detail page with full description, allergens, and producer info."""
    product = get_object_or_404(Products, id=product_id)
    producer = product.producer

    # Allergen labels for display
    ALLERGEN_LABELS = {
        'celery': 'Celery', 'gluten': 'Gluten', 'lupin': 'Lupin',
        'crustaceans': 'Crustaceans', 'milk': 'Milk', 'sulphur_dioxide': 'Sulphur Dioxide',
        'sesame': 'Sesame', 'molluscs': 'Molluscs', 'mustard': 'Mustard',
        'nuts': 'Nuts', 'egg': 'Egg', 'fish': 'Fish',
        'soybeans': 'Soybeans', 'peanuts': 'Peanuts',
    }

    # Parse allergens from string representation
    allergen_display = ''
    if product.allergens:
        try:
            allergen_list = ast.literal_eval(product.allergens) if isinstance(product.allergens, str) else product.allergens
            allergen_display = ', '.join(ALLERGEN_LABELS.get(a, a) for a in allergen_list)
        except (ValueError, SyntaxError):
            allergen_display = product.allergens

    # Calculate distance
    distance = None
    drive_time = None
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    if producer.latitude and producer.longitude:
        ref_lat, ref_lng = 51.4545, -2.5879
        if user_id and user_type == 'customer':
            customer = Accounts.objects.filter(id=user_id).first()
            if customer and customer.latitude and customer.longitude:
                ref_lat, ref_lng = customer.latitude, customer.longitude
        result = get_driving_distance(ref_lat, ref_lng, producer.latitude, producer.longitude)
        distance = round(result['distance_miles'], 1)
        drive_time = result['duration_minutes']

    # get reviews for this product
    reviews = Reviews.objects.filter(product=product).order_by('-created_at')
    user_review = None
    review_list = []
    # show reviews in product detail page
    for review in reviews:
        if review.customer.id != user_id:
            review_list.append({
                'customer': review.customer.name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at,
            })
        else:
            user_review = {
                'customer': review.customer.name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at,
            }
    if user_review is None:
        user_can_review = Orders.objects.filter(
        user__id=user_id,
        order_status='confirmed',
        items__product__id=product_id,
    ).exists()

    return render(request, 'home/product_detail.html', {
        'product': product,
        'producer': producer,
        'distance': distance,
        'drive_time': drive_time,
        'reviews': review_list,
        'user_review': user_review,
        'can_review': user_can_review,
        'allergens': allergen_display,
    })


def producers(request):
    """Producers page with map and food miles calculation."""
    certification = request.GET.get('certification', '')

    if certification:
        all_producers = Producers.objects.filter(certifications=certification, is_active=True).distinct()
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

    # Use customer location as origin, or Bristol centre if not logged in
    origin_lat = customer_lat if customer_lat else default_lat
    origin_lng = customer_lng if customer_lng else default_lng

    all_producers_list = list(all_producers)

    # Batch a single Distance Matrix call for all producers that have coordinates
    coords_producers = [(i, p) for i, p in enumerate(all_producers_list) if p.latitude and p.longitude]
    driving_results = {}
    if coords_producers:
        destinations = [{'lat': p.latitude, 'lng': p.longitude} for _, p in coords_producers]
        batch = get_driving_distances_batch(origin_lat, origin_lng, destinations)
        driving_results = {i: r for (i, _), r in zip(coords_producers, batch)}

    producer_list = []
    for i, producer in enumerate(all_producers_list):
        result = driving_results.get(i)
        distance = round(result['distance_miles'], 1) if result and result['distance_miles'] is not None else None
        drive_time = result['duration_minutes'] if result else None

        producer_list.append({
            'id': producer.id,
            'name': producer.business_name,
            'description': producer.description,
            'address': producer.address,
            'postal_code': producer.postal_code,
            'latitude': producer.latitude,
            'longitude': producer.longitude,
            'distance': distance,
            'drive_time': drive_time,
            'collection_available': producer.collection_available,
            'delivery_available': producer.delivery_available,
            'image_url': producer.business_image.url if producer.business_image else None,
        })

    # Sort by distance if available
    producer_list.sort(key=lambda p: p['distance'] if p['distance'] is not None else 9999)

    return render(request, 'home/producers.html', {
        'producers': producer_list,
        'selected_certification': certification,
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
    drive_time = None
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')
    if producer.latitude and producer.longitude:
        ref_lat, ref_lng = 51.4545, -2.5879
        if user_id and user_type == 'customer':
            customer = Accounts.objects.filter(id=user_id).first()
            if customer and customer.latitude and customer.longitude:
                ref_lat, ref_lng = customer.latitude, customer.longitude
        result = get_driving_distance(ref_lat, ref_lng, producer.latitude, producer.longitude)
        distance = round(result['distance_miles'], 1)
        drive_time = result['duration_minutes']

    return render(request, 'home/store.html', {
        'producer': producer,
        'products': products,
        'distance': distance,
        'drive_time': drive_time,
    })

def add_review(request, product_id):
    """Handle submission of a new review for a product."""
    product = get_object_or_404(Products, id=product_id)

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        user_type = request.session.get('user_type')

        if user_id and user_type == 'customer':
            customer = Accounts.objects.filter(id=user_id).first()
            if customer:
                rating = int(request.POST.get('rating', 5))
                comment = request.POST.get('comment', '')
                Reviews.objects.create(product=product, customer=customer, rating=rating, comment=comment)

    # After adding review, redirect back to product detail page
    return product_detail(request, product_id)
