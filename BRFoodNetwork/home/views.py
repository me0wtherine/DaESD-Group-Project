from django.shortcuts import render


def home(request):
    """Homepage with popular items and nearby producers (placeholder data)."""
    popular_items = [
        {'name': 'Organic Carrots', 'farm': 'Green Acres Farm', 'distance': 5, 'price': '2.50'},
        {'name': 'Sourdough Loaf', 'farm': 'Bristol Bakery', 'distance': 3, 'price': '4.00'},
        {'name': 'Free Range Eggs', 'farm': 'Hillside Farm', 'distance': 7, 'price': '3.20'},
        {'name': 'Raw Honey', 'farm': 'Avon Apiaries', 'distance': 8, 'price': '6.50'},
        {'name': 'Goat Cheese', 'farm': 'Mendip Dairy', 'distance': 12, 'price': '5.00'},
        {'name': 'Apple Juice', 'farm': 'Chew Valley Orchards', 'distance': 10, 'price': '3.80'},
    ]

    nearby_producers = [
        {'name': 'Green Acres Farm', 'distance': 5},
        {'name': 'Bristol Bakery', 'distance': 3},
        {'name': 'Hillside Farm', 'distance': 7},
        {'name': 'Avon Apiaries', 'distance': 8},
        {'name': 'Mendip Dairy', 'distance': 12},
    ]

    return render(request, 'home/home.html', {
        'popular_items': popular_items,
        'nearby_producers': nearby_producers,
    })


def welcome(request):
    """Welcome / landing page for unauthenticated users."""
    return render(request, 'home/welcome.html')
