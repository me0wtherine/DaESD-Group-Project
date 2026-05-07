import json
from datetime import timedelta
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from accounts.models import Producers
from accounts.geocoding import geocode_address, is_within_bristol_radius
from products.models import Products
from notifications.models import Notification
from .forms import StoreInfoForm, ProductForm

from django.http import HttpResponse
from django.template.loader import render_to_string

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
            updated = form.save(commit=False)
            # Enforce 20-mile Bristol radius (straight-line / Haversine) on any address change
            lat, lng = geocode_address(updated.address, updated.postal_code)
            if lat is None or lng is None:
                messages.error(request, 'Could not verify that address. Please enter a valid UK address and postcode.')
            elif not is_within_bristol_radius(lat, lng):
                messages.error(request, 'That address is outside the 20-mile Bristol service area (straight-line distance from city centre).')
            else:
                updated.latitude = lat
                updated.longitude = lng
                updated.save()
                messages.success(request, 'Store information updated successfully!')
                return redirect('producer_dashboard')
    else:
        form = StoreInfoForm(instance=producer)

    return render(request, 'producers/edit_store.html', {
        'form': form,
        'producer': producer,
    })


@producer_required
def producer_products(request):
    """Dedicated page listing all products for the logged-in producer."""
    producer = get_object_or_404(Producers, id=request.session['user_id'])
    products = Products.objects.filter(producer=producer)
    return render(request, 'producers/producer_products.html', {
        'producer': producer,
        'products': products,
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

@producer_required
def producer_orders(request):
    """Display all orders that contain products from the logged-in producer."""
    from orders.models import OrderItem
    from accounts.geocoding import get_driving_distance

    producer = get_object_or_404(Producers, id=request.session['user_id'])

    order_items = (
        OrderItem.objects
        .select_related('order', 'product', 'order__user')
        .filter(product__producer=producer)
        .order_by('-order__order_date')
    )

    # Calculate food miles per order item
    items_with_miles = []
    for item in order_items:
        food_miles = None
        drive_time = None
        customer = item.order.user
        if (producer.latitude and producer.longitude and
                getattr(customer, 'latitude', None) and getattr(customer, 'longitude', None)):
            result = get_driving_distance(
                producer.latitude, producer.longitude,
                customer.latitude, customer.longitude
            )
            food_miles = round(result['distance_miles'], 1)
            drive_time = result['duration_minutes']
        items_with_miles.append({'item': item, 'food_miles': food_miles, 'drive_time': drive_time})

    return render(request, 'producers/producers_orders.html', {
        'producer': producer,
        'order_items_with_miles': items_with_miles,
    })


@producer_required
def surplus_deals(request):
    """Manage surplus deals – list products and let producers set deal prices for items near best-before."""
    from datetime import date
    from decimal import Decimal, InvalidOperation

    producer = get_object_or_404(Producers, id=request.session['user_id'])

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Products, id=product_id, producer=producer)
        action = request.POST.get('action')

        if action == 'set_deal':
            best_before = request.POST.get('best_before', '').strip()
            surplus_price = request.POST.get('surplus_price', '').strip()

            if not best_before:
                messages.error(request, 'Please set a best-before date.')
                return redirect('surplus_deals')
            if not surplus_price:
                messages.error(request, 'Please enter a deal price.')
                return redirect('surplus_deals')

            try:
                deal_price = Decimal(surplus_price)
            except (InvalidOperation, ValueError):
                messages.error(request, 'Invalid price entered.')
                return redirect('surplus_deals')

            if deal_price <= 0 or deal_price >= product.price:
                messages.error(request, 'Deal price must be between £0.01 and the original price.')
                return redirect('surplus_deals')

            product.best_before = best_before
            product.surplus_price = deal_price
            product.is_surplus = True
            product.save()
            messages.success(request, f'"{product.name}" is now on a surplus deal at £{deal_price}!')

        elif action == 'remove_deal':
            product.is_surplus = False
            product.surplus_price = None
            product.save()
            messages.success(request, f'Surplus deal removed from "{product.name}".')

        return redirect('surplus_deals')

    # GET – split into active deals and eligible products
    all_products = Products.objects.filter(producer=producer, is_available=True)
    active_deals = all_products.filter(is_surplus=True).order_by('best_before')
    available_for_deals = all_products.filter(is_surplus=False).order_by('name')

    return render(request, 'producers/surplus_deals.html', {
        'producer': producer,
        'active_deals': active_deals,
        'available_for_deals': available_for_deals,
        'today': date.today().isoformat(),
    })


@producer_required
def producer_payouts(request):
    """Display weekly settlements and payouts for the logged-in producer"""
    import csv
    from django.http import HttpResponse
    from orders.models import Orders
    from datetime import datetime, timedelta, date
    from django.utils import timezone
    from django.db.models import Sum
    from django.db.models import Sum, F, DecimalField, ExpressionWrapper
    from orders.models import OrderItem
    from django.db.models import Q
    
    producer = get_object_or_404(Producers, id=request.session['user_id'])
    
    # Get the start/end dates of the current week
    week_offset = int(request.GET.get('week', 0))
    today = datetime.now().date()
    target_date = today + timedelta(weeks=week_offset)
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)

    # Get all orders for that week's settlement calculations
    all_orders = Orders.objects.filter(
        order_date__date__gte=week_start,
        order_date__date__lte=week_end,
        items__product__producer=producer,
        order_status='ready',
    ).distinct().order_by('order_date')
    
    # Calculate settlement data
    settlements = []
    total_orders_value = 0
    total_commission = 0
    total_payout = 0

    for order in all_orders:
        order_value = float(order.total_price)
        commission = order_value * 0.05  # 5% network commission
        payout = order_value * 0.95  # 95% producer payment

        total_orders_value += order_value
        total_commission += commission
        total_payout += payout

        settlements.append({
            'order': order,
            'order_value': order_value,
            'commission': commission,
            'payout': payout,
            'status': order.settlement_status,
        })

    # Calculate total payments for the tax year
    tax_year_start, tax_year_label = get_tax_year_start(today)
    
    tax_year_total = 0
    tax_year_orders = Orders.objects.filter(
        order_date__date__gte=tax_year_start,
        items__product__producer=producer,
    ).exclude(
        order_status='cancelled',
    ).distinct()

    for order in tax_year_orders:
        # Only sum items belonging to this producer, not the full order total
        producer_items = order.items.filter(product__producer=producer)
        for item in producer_items:
            tax_year_total += float(item.price) * float(item.quantity) * 0.95

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"payment_report_{week_start}_to_{week_end}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Header block
        writer.writerow(['LocalHarvest Network — Producer Payment Report'])
        writer.writerow([''])
        writer.writerow(['Producer:', producer.business_name])
        writer.writerow(['Settlement Week:', f"{week_start.strftime('%d %b %Y')} – {week_end.strftime('%d %b %Y')}"])
        writer.writerow(['Report Generated:', datetime.now().strftime('%d %b %Y %H:%M')])
        writer.writerow(['Tax Year:', f"{tax_year_label}/{tax_year_label + 1}"])
        writer.writerow([''])

        # Payment summary
        writer.writerow(['PAYMENT SUMMARY'])
        writer.writerow(['Total Orders Value', f"£{total_orders_value:.2f}"])
        writer.writerow(['Network Commission (5%)', f"-£{total_commission:.2f}"])
        writer.writerow(['Your Payment This Week (95%)', f"£{total_payout:.2f}"])
        writer.writerow(['Tax Year Running Total', f"£{tax_year_total:.2f}"])
        writer.writerow([''])

        # Order breakdown
        writer.writerow(['ORDER BREAKDOWN'])
        writer.writerow(['Order No.', 'Date', 'Customer', 'Items', 'Order Value', 'Commission (5%)', 'Your Payment (95%)', 'Status'])

        for s in settlements:
            order = s['order']
            # Anonymise customer name to first name + initial
            customer = order.user.name if order.user else 'Unknown'
            parts = customer.split()
            anon_name = f"{parts[0]} {parts[1][0]}." if len(parts) > 1 else parts[0]

            # Get items belonging to this producer
            items_list = ', '.join(
                f"{item.product.name} x{item.quantity}"
                for item in order.items.filter(product__producer=producer)
            )

            status = 'Processed' if s['status'] == 'processed' else 'Pending Bank Transfer'

            writer.writerow([
                f"#{order.id:05d}",
                order.order_date.strftime('%d/%m/%Y'),
                anon_name,
                items_list,
                f"£{s['order_value']:.2f}",
                f"-£{s['commission']:.2f}",
                f"£{s['payout']:.2f}",
                status,
            ])

        # Totals row
        writer.writerow(['', '', '', 'TOTAL', f"£{total_orders_value:.2f}", f"-£{total_commission:.2f}", f"£{total_payout:.2f}", ''])
        writer.writerow([''])

        # Compliance footer
        writer.writerow([f"Report Reference: RPT-{tax_year_label}{tax_year_label+1}-{producer.id}-W{week_start.strftime('%W')}"])

        return response
    
    return render(request, 'producers/producer_payouts.html', {
        'producer': producer,
        'settlements': settlements,
        'total_orders_value': total_orders_value,
        'total_commission': total_commission,
        'total_payout': total_payout,
        'week_start_date': week_start,
        'week_end_date': week_end,
        'week_offset': week_offset,
        'tax_year_start': tax_year_start,
        'tax_year_label': tax_year_label,
        'tax_year_total': tax_year_total,
    })

# Calculate the tax year
def get_tax_year_start(today):
    from datetime import date

    year = today.year
    if today < date(year, 4, 6):
        return date(year - 1, 4, 6), year - 1
    return date(year, 4, 6), year

@producer_required
def weekly_settlements(request):
    """Display weekly payment settlements for the logged-in producer."""
    from payments.models import Payments

    producer = get_object_or_404(Producers, id=request.session['user_id'])

    payment_records = (
        Payments.objects
        .filter(producer=producer)
        .select_related('order', 'order__user')
        .order_by('-order__order_date')
    )

    weeks = {}
    for payment in payment_records:
        order_date = payment.order.order_date
        week_start = (order_date - timedelta(days=order_date.weekday())).date()
        week_key = week_start.isoformat()

        if week_key not in weeks:
            weeks[week_key] = {
                'week_starting': week_start,
                'payments': [],
                'total_value': 0,
                'total_commission': 0,
                'total_payout': 0,
            }

        order_value = float(payment.producer_payment + payment.network_commission)
        weeks[week_key]['payments'].append({
            'order': payment.order,
            'order_value': order_value,
            'commission': float(payment.network_commission),
            'payout': float(payment.producer_payment),
            'settlement_status': payment.order.settlement_status,
            'settlement_status_display': payment.order.get_settlement_status_display(),
        })
        weeks[week_key]['total_value'] += order_value
        weeks[week_key]['total_commission'] += float(payment.network_commission)
        weeks[week_key]['total_payout'] += float(payment.producer_payment)

    sorted_weeks = sorted(weeks.values(), key=lambda w: w['week_starting'], reverse=True)
    grand_total_value = sum(w['total_value'] for w in sorted_weeks)
    grand_total_commission = sum(w['total_commission'] for w in sorted_weeks)
    grand_total_payout = sum(w['total_payout'] for w in sorted_weeks)

    return render(request, 'producers/weekly_settlements.html', {
        'producer': producer,
        'weeks': sorted_weeks,
        'grand_total_value': grand_total_value,
        'grand_total_commission': grand_total_commission,
        'grand_total_payout': grand_total_payout,
    })


@producer_required
@require_POST
def update_order_status(request, order_id):
    """Allow a producer to advance the status of an order containing their products."""
    from orders.models import Orders, OrderItem

    producer = get_object_or_404(Producers, id=request.session['user_id'])
    order = get_object_or_404(Orders, id=order_id)

    # Verify this producer has items in this order
    has_items = OrderItem.objects.filter(order=order, product__producer=producer).exists()
    if not has_items:
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('producer_orders')

    new_status = request.POST.get('order_status', '')
    valid_statuses = [c[0] for c in Orders.ORDER_STATUS_CHOICES]
    if new_status not in valid_statuses:
        messages.error(request, 'Invalid order status.')
        return redirect('producer_orders')

    order.order_status = new_status
    order.save()
    if new_status == 'ready':
        Notification.objects.create(
            customer=order.user,
            message=f"Your order #{order.id:05d} from {producer.business_name} is ready for pickup. Total: £{order.total_price}. Ordered on {order.order_date.date()}."
        )
    messages.success(request, f'Order #{order.id:05d} status updated to {order.get_order_status_display()}.')
    return redirect('producer_orders')