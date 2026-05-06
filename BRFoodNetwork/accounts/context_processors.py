from accounts.models import Accounts, Producers, Admins
from notifications.models import Notification


def user_context(request):
    """Add logged-in user information and notifications to template context."""
    context = {
        "user_id": None,
        "user_name": None,
        "user_type": None,
        "notifications": [],
        "unread_count": 0,
    }

    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type")

    if not user_id:
        return context

    try:
        if user_type == "customer":
            user = Accounts.objects.get(id=user_id)
            context["user_name"] = user.name
            context["user_type"] = "customer"

            context["notifications"] = Notification.objects.filter(
                customer=user,
                is_read=False
            ).order_by("-created_at")[:5]

            context["unread_count"] = Notification.objects.filter(
                customer=user,
                is_read=False
            ).count()

        elif user_type == "producer":
            producer = Producers.objects.get(id=user_id)
            context["user_name"] = producer.business_name
            context["user_type"] = "producer"
            context["notifications"] = Notification.objects.filter(
                producer=producer,
                is_read=False
            ).order_by("-created_at")[:5]

            context["unread_count"] = Notification.objects.filter(
                producer=producer,
                is_read=False
            ).count()

        elif user_type == "admin":
            admin = Admins.objects.get(id=user_id)
            context["user_name"] = admin.name
            context["user_type"] = "admin"
            """context["notifications"] = Notification.objects.filter(
                admin=admin,
                is_read=False
            ).order_by("-created_at")[:5]

            context["unread_count"] = Notification.objects.filter(
                admin=admin,
                is_read=False
            ).count()"""

    except (Accounts.DoesNotExist, Producers.DoesNotExist, Admins.DoesNotExist):
        request.session.flush()

    return context