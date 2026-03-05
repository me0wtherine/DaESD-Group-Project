from decimal import Decimal
from accounts.models import Accounts
from cart.models import Cart


def cart_context(request):
    cart_items = []
    cart_total = Decimal("0.00")

    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type")
    if user_id and user_type == "customer":
        customer = Accounts.objects.filter(id=user_id).first()

        if customer:
            cart, _ = Cart.objects.get_or_create(user=customer)

            items = cart.items.select_related("product").all()

            for item in items:
                line_total = item.product.price * item.quantity

                cart_items.append({
                    "id": item.id,
                    "product_id": item.product.id,
                    "name": item.product.name,
                    "price": item.product.price,
                    "quantity": item.quantity,
                    "line_total": line_total,
                })

                cart_total += line_total
    return {
        "cart_items": cart_items,
        "cart_total": cart_total,
    }