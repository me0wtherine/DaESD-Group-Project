from decimal import Decimal
from django.shortcuts import render, redirect

from accounts.models import Accounts
from cart.models import Cart


def cart_detail(request):
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type", "customer")

    #so logged in customers can see their baskey
    if not user_id or user_type != "customer":
        return redirect("welcome")

    customer = Accounts.objects.filter(id=user_id).first()
    if not customer:
        request.session.flush()
        return redirect("welcome")

    cart, _ = Cart.objects.get_or_create(user=customer)
    items = cart.items.select_related("product").all()

    total = Decimal("0.00")
    for item in items:
        total += item.product.price * item.quantity

    return render(request, "cart/detail.html", {"items": items, "total": total})