"""
Signal handlers for the products app.

These hooks run automatically on model events and add functionality
without modifying existing views — keeping order/payment code untouched.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='orders.OrderItem')
def decrement_stock_and_alert(sender, instance, created, **kwargs):
    """
    When a new OrderItem is saved:
      1. Reduce the product's stock_quantity by the ordered quantity
         (never below zero).
      2. If the new stock is at or below low_stock_threshold,
         create a Notification for the producer (TC-023).
    """
    if not created:
        return

    product = instance.product
    quantity = instance.quantity or 0
    new_stock = max(0, product.stock_quantity - quantity)
    product.stock_quantity = new_stock

    # Auto-disable when fully out of stock
    if new_stock == 0:
        product.is_available = False

    product.save(update_fields=['stock_quantity', 'is_available'])

    # Low-stock alert
    if 0 < new_stock <= product.low_stock_threshold:
        try:
            from notifications.models import Notification
            Notification.objects.create(
                producer=product.producer,
                title='Low Stock Alert',
                message=(
                    f'{product.name} is running low — only {new_stock} '
                    f'{product.unit} remaining (threshold: {product.low_stock_threshold}).'
                ),
            )
        except Exception:
            # Never let signal failure block order creation
            pass
    elif new_stock == 0:
        try:
            from notifications.models import Notification
            Notification.objects.create(
                producer=product.producer,
                title='Out of Stock',
                message=f'{product.name} is now out of stock and has been hidden from customers.',
            )
        except Exception:
            pass
