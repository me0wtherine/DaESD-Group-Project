from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from accounts.models import Accounts
from cart.models import Cart, CartItem
from products.models import Products


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