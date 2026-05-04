import uuid
import stripe
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from accounts.models import Accounts
from accounts.geocoding import haversine
from cart.models import Cart
from orders.models import Orders, OrderItem
from payments.models import Payments, WeeklyPayment

stripe.api_key = settings.STRIPE_SECRET_KEY
COMMISSION_RATE = Decimal('0.05')


def _is_stripe_configured():
    """Check if real Stripe keys are configured (not placeholders)."""
    key = settings.STRIPE_SECRET_KEY
    return key and key != 'sk_test_placeholder'


def payment_page(request):
    """Show payment confirmation page with order summary and Stripe pay button."""
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type', 'customer')

    if not user_id or user_type != 'customer':
        return redirect('welcome')

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        request.session.flush()
        return redirect('welcome')

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        return redirect('cart:checkout')

    cart = Cart.objects.filter(user=customer).first()
    if not cart:
        return redirect('cart:detail')

    items = cart.items.select_related('product', 'product__producer').all()
    if not items.exists():
        return redirect('cart:detail')

    # Bypass payment page entirely when Stripe is not configured (dev testing)
    if not _is_stripe_configured():
        fake_session_id = f'sim_{uuid.uuid4().hex}'
        request.session['stripe_session_id'] = fake_session_id
        return redirect(f'/payments/success/?session_id={fake_session_id}')

    # Group items by producer for multi-vendor transparency
    producers_items = {}
    total = Decimal('0.00')
    for item in items:
        producer = item.product.producer
        subtotal = item.product.price * item.quantity
        total += subtotal

        if producer.id not in producers_items:
            producers_items[producer.id] = {
                'producer': producer,
                'items': [],
                'subtotal': Decimal('0.00'),
                'food_miles': None,
            }
            # Calculate food miles from customer to producer
            if customer.latitude and customer.longitude and producer.latitude and producer.longitude:
                producers_items[producer.id]['food_miles'] = round(
                    haversine(customer.latitude, customer.longitude, producer.latitude, producer.longitude), 1
                )
        producers_items[producer.id]['items'].append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.product.price,
            'subtotal': subtotal,
        })
        producers_items[producer.id]['subtotal'] += subtotal

    return render(request, 'cart/payment.html', {
        'customer': customer,
        'checkout_data': checkout_data,
        'producers_items': producers_items.values(),
        'total': total,
        'stripe_configured': _is_stripe_configured(),
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@require_http_methods(['POST'])
def create_checkout_session(request):
    """Create a Stripe Checkout Session and redirect to Stripe hosted payment page."""
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type', 'customer')

    if not user_id or user_type != 'customer':
        return redirect('welcome')

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        return redirect('welcome')

    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        return redirect('cart:checkout')

    cart = Cart.objects.filter(user=customer).first()
    if not cart:
        return redirect('cart:detail')

    items = cart.items.select_related('product', 'product__producer').all()
    if not items.exists():
        return redirect('cart:detail')

    domain = request.build_absolute_uri('/')[:-1]

    # Simulation mode when Stripe keys are not configured
    if not _is_stripe_configured():
        fake_session_id = f'sim_{uuid.uuid4().hex}'
        request.session['stripe_session_id'] = fake_session_id
        return redirect(f'/payments/success/?session_id={fake_session_id}')

    # Build Stripe line items
    line_items = []
    for item in items:
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': item.product.name,
                    'description': f'From {item.product.producer.business_name}',
                },
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=customer.email,
            success_url=f'{domain}/payments/success/?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{domain}/payments/cancel/',
            metadata={
                'customer_id': str(customer.id),
            },
        )
        request.session['stripe_session_id'] = session.id
        return redirect(session.url)

    except Exception as e:
        messages.error(request, f'Payment error: {e}')
        return redirect('payments:payment_page')


def payment_success(request):
    """Handle successful payment - create order and payment records."""
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type', 'customer')

    if not user_id or user_type != 'customer':
        return redirect('welcome')

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        return redirect('welcome')

    session_id = request.GET.get('session_id', '')
    checkout_data = request.session.get('checkout_data')

    if not session_id or not checkout_data:
        return redirect('cart:detail')

    # Idempotency - don't create duplicate orders
    existing = Orders.objects.filter(stripe_session_id=session_id).first()
    if existing:
        return render(request, 'cart/order_confirmed.html', {'order': existing})

    is_simulated = session_id.startswith('sim_')

    # Verify payment with Stripe (skip in simulation mode)
    if not is_simulated:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status != 'paid':
                messages.error(request, 'Payment was not completed. Please try again.')
                return redirect('cart:checkout')
        except Exception:
            messages.error(request, 'Could not verify payment. Please contact support.')
            return redirect('cart:detail')

    # Get cart items
    cart = Cart.objects.filter(user=customer).first()
    if not cart:
        return redirect('cart:detail')

    items = cart.items.select_related('product', 'product__producer').all()
    if not items.exists():
        return redirect('home')

    # Calculate total
    total = Decimal('0.00')
    for item in items:
        total += item.product.price * item.quantity

    # Parse delivery date
    delivery_date = None
    try:
        delivery_date = datetime.strptime(checkout_data.get('delivery_date', ''), '%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    # Create the order
    order = Orders.objects.create(
        user=customer,
        delivery_address=checkout_data.get('delivery_address', ''),
        fulfillment_type=checkout_data.get('fulfillment_type', 'delivery'),
        delivery_date=delivery_date,
        total_price=total,
        order_status='confirmed',
        payment_method='stripe' if not is_simulated else 'simulated',
        stripe_session_id=session_id,
        is_recurring=checkout_data.get('is_recurring', False),
        recurring_frequency=checkout_data.get('recurring_frequency',''),
        recurring_start_date=checkout_data.get('recurring_start_date') or None,

    )

    # Create order items and track per-producer totals
    producer_totals = {}
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )
        producer = item.product.producer
        item_total = item.product.price * item.quantity
        if producer.id not in producer_totals:
            producer_totals[producer.id] = {
                'producer': producer,
                'total': Decimal('0.00'),
            }
        producer_totals[producer.id]['total'] += item_total

    # Create Payment records per producer with 5% network commission
    for data in producer_totals.values():
        producer_total = data['total']
        commission = (producer_total * COMMISSION_RATE).quantize(Decimal('0.01'))
        producer_payment = producer_total - commission
        Payments.objects.create(
            order=order,
            producer=data['producer'],
            network_commission=commission,
            producer_payment=producer_payment,
        )

    # Clear cart and session checkout data
    cart.items.all().delete()
    request.session.pop('checkout_data', None)
    request.session.pop('stripe_session_id', None)

    return render(request, 'cart/order_confirmed.html', {'order': order})


def payment_cancel(request):
    """Handle cancelled Stripe payment."""
    messages.info(request, 'Payment was cancelled. Your cart items are still saved.')
    return redirect('cart:checkout')


@csrf_exempt
@require_http_methods(['POST'])
def stripe_webhook(request):
    """Handle Stripe webhook events for payment confirmation."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order = Orders.objects.filter(stripe_session_id=session['id']).first()
        if order and order.order_status == 'pending':
            order.order_status = 'confirmed'
            order.save()

    return HttpResponse(status=200)
