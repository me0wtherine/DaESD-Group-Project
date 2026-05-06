from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.models import Accounts
from cart.models import Cart, CartItem
from products.models import Products
from orders.models import Orders, OrderItem
from django.http import JsonResponse


def _get_customer_cart(user_id):
    """Get the logged-in customer's cart."""
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

    items = cart.items.select_related("product", "product__producer").all()

    total = Decimal("0.00")
    producer_groups = {}

    for item in items:
        total += item.product.price * item.quantity

        producer = item.product.producer

        if producer.id not in producer_groups:
            producer_groups[producer.id] = {
                "producer": producer,
                "items": [],
            }

        producer_groups[producer.id]["items"].append(item)

    return render(request, "cart/detail.html", {
        "items": items,
        "producer_groups": producer_groups.values(),
        "total": total,
    })


@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    """Add a product to the logged-in customer's cart."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("welcome")

    product = get_object_or_404(Products, id=product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    # send user back to the page they clicked from
    return redirect(request.META.get("HTTP_REFERER", "cart:detail"))


@require_http_methods(["POST"])
def update_quantity(request, item_id):
    """Update quantity of an item already in the cart."""
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    if not user_id or user_type != "customer":
        return redirect("welcome")

    cart = _get_customer_cart(user_id)
    if not cart:
        return redirect("welcome")

    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        quantity = 1

    item.quantity = quantity
    item.save()

    return JsonResponse({"status": "ok"})


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

    item = CartItem.objects.filter(id=item_id, cart=cart).first()
    if item:
        item.delete()

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

    items = cart.items.select_related("product", "product__producer").all()
    if not items.exists():
        return redirect("cart:detail")

    producer_groups = {}
    total = Decimal("0.00")

    for item in items:
        line_total = item.product.price * item.quantity
        total += line_total

        producer = item.product.producer

        if producer.id not in producer_groups:
            producer_groups[producer.id] = {
                "producer": producer,
                "items": [],
                "subtotal": Decimal("0.00"),
            }

        producer_groups[producer.id]["items"].append(item)
        producer_groups[producer.id]["subtotal"] += line_total

    min_date = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d")

    if request.method == "POST":
        address = request.POST.get("address", "").strip()
        postcode = request.POST.get("postcode", "").strip()
        fulfillment_type = request.POST.get("fulfillment_type", "delivery")

        same_delivery_date = request.POST.get("same_delivery_date") == "yes"
        common_delivery_date = request.POST.get("common_delivery_date", "")

        is_recurring = request.POST.get("is_recurring") == "yes"
        recurring_frequency = request.POST.get("recurring_frequency", "")
        recurring_start_date = request.POST.get("recurring_start_date", "")

        if not address or not postcode:
            return render(request, "cart/checkout.html", {
                "items": items,
                "producer_groups": producer_groups.values(),
                "total": total,
                "customer": customer,
                "min_date": min_date,
                "error": "Address and postcode are required.",
            })

        delivery_address = f"{address}, {postcode}"

        if fulfillment_type not in ["delivery", "collection"]:
            return render(request, "cart/checkout.html", {
                "items": items,
                "producer_groups": producer_groups.values(),
                "total": total,
                "customer": customer,
                "min_date": min_date,
                "error": "Invalid fulfillment type.",
            })

        producer_delivery_dates = {}

        for group in producer_groups.values():
            producer = group["producer"]

            if same_delivery_date:
                delivery_date_str = common_delivery_date
            else:
                delivery_date_str = request.POST.get(f"delivery_date_{producer.id}", "")

            try:
                delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
            except ValueError:
                return render(request, "cart/checkout.html", {
                    "items": items,
                    "producer_groups": producer_groups.values(),
                    "total": total,
                    "customer": customer,
                    "min_date": min_date,
                    "error": "Please select a valid delivery date for each producer.",
                })

            now = datetime.now()
            min_delivery_date = now + timedelta(hours=48)

            if delivery_date < min_delivery_date.replace(hour=0, minute=0, second=0, microsecond=0):
                return render(request, "cart/checkout.html", {
                    "items": items,
                    "producer_groups": producer_groups.values(),
                    "total": total,
                    "customer": customer,
                    "min_date": min_date,
                    "error": "Delivery/collection date must be at least 48 hours from now.",
                })

            producer_delivery_dates[str(producer.id)] = delivery_date_str

        request.session["checkout_data"] = {
            "delivery_address": delivery_address,
            "fulfillment_type": fulfillment_type,
            "same_delivery_date": same_delivery_date,
            "common_delivery_date": common_delivery_date,
            "producer_delivery_dates": producer_delivery_dates,
            "is_recurring": is_recurring,
            "recurring_frequency": recurring_frequency,
            "recurring_start_date": recurring_start_date,
        }

        return redirect("payments:payment_page")

    return render(request, "cart/checkout.html", {
        "items": items,
        "producer_groups": producer_groups.values(),
        "total": total,
        "customer": customer,
        "min_date": min_date,
    })