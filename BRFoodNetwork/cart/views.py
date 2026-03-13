from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from accounts.models import Accounts
from cart.models import Cart, CartItem
from products.models import Products
from orders.models import Orders, OrderItem


def _get_customer_cart(user_id):
    """Helper function to get customer's cart."""
    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        return None
    cart, _ = Cart.objects.get_or_create(user=customer)
    return cart


def cart_detail(request):
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    # so logged in customers can see their basket
    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        request.session.flush()
        return redirect("welcome")

    items = cart.items.select_related("product").all()

    total = Decimal("0.00")
    for item in items:
        total += item.product.price * item.quantity

    return render(request, "cart/detail.html", {"items": items, "total": total})


@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    """Add a product to the cart."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("welcome")

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    try:
        product = Products.objects.get(id=product_id)
    except Products.DoesNotExist:
        return redirect("cart:detail")

    # Add or update item in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return redirect("cart:detail")


@require_http_methods(["POST"])
def update_quantity(request, item_id):
    """Update the quantity of an item in the cart."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("welcome")

    try:
        item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return redirect("cart:detail")

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    item.quantity = quantity
    item.save()

    return redirect("cart:detail")


@require_http_methods(["POST"])
def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("welcome")

    try:
        item = CartItem.objects.get(id=item_id, cart=cart)
        item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect("cart:detail")


def checkout(request):
    """Handle checkout process."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        request.session.flush()
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("cart:detail")

    items = cart.items.select_related("product").all()
    if not items.exists():
        return redirect("cart:detail")

    if request.method == "POST":
        address = request.POST.get("address", "").strip()
        postcode = request.POST.get("postcode", "").strip()
        fulfillment_type = request.POST.get("fulfillment_type", "delivery")
        delivery_date_str = request.POST.get("delivery_date", "")

        # Validate inputs
        if not address or not postcode:
            return render(
                request,
                "cart/checkout.html",
                {
                    "items": items,
                    "customer": customer,
                    "error": "Address and postcode are required.",
                },
            )
        
        # Combine address and postcode
        delivery_address = f"{address}, {postcode}"

        if fulfillment_type not in ["delivery", "collection"]:
            return render(
                request,
                "cart/checkout.html",
                {"items": items, "customer": customer, "error": "Invalid fulfillment type."},
            )

        # Validate delivery date
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
        except ValueError:
            return render(
                request,
                "cart/checkout.html",
                {
                    "items": items,
                    "customer": customer,
                    "error": "Invalid delivery date format.",
                },
            )

        # Check if date is at least 48 hours in the future
        now = datetime.now()
        min_delivery_date = now + timedelta(hours=48)
        if delivery_date < min_delivery_date.replace(hour=0, minute=0, second=0, microsecond=0):
            return render(
                request,
                "cart/checkout.html",
                {
                    "items": items,
                    "customer": customer,
                    "error": "Delivery/collection date must be at least 48 hours from now.",
                },
            )

        # Calculate total
        total = Decimal("0.00")
        for item in items:
            total += item.product.price * item.quantity

        # Create order
        order = Orders.objects.create(
            user=customer,
            delivery_address=delivery_address,
            fulfillment_type=fulfillment_type,
            delivery_date=delivery_date,
            total_price=total,
            order_status="pending",
        )

        # Create order items
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        # Clear the cart
        cart.items.all().delete()

        return render(request, "cart/order_confirmed.html", {"order": order})

    # Calculate total for display
    total = Decimal("0.00")
    for item in items:
        total += item.product.price * item.quantity

    # Calculate minimum delivery date (48 hours from now)
    min_date = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d")

    return render(
        request,
        "cart/checkout.html",
        {
            "items": items,
            "total": total,
            "customer": customer,
            "min_date": min_date,
        },
    )