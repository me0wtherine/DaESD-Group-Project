from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from accounts.models import Accounts
from .models import Notification


def notifications(request):
    """Display all notifications for the logged-in customer."""
    if 'user_id' not in request.session or request.session.get('user_type') != 'customer':
        messages.error(request, 'You must be logged in as a customer to view notifications.')
        return redirect('home')
    
    user = get_object_or_404(Accounts, id=request.session['user_id'])
    user_notifications = Notification.objects.filter(customer=user).order_by('-created_at')
    
    # Mark all notifications as read when viewing the notification center
    unread_notifications = user_notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    return render(request, 'notifications/notification_center.html', {
        'notifications': user_notifications,
    })


@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    if 'user_id' not in request.session or request.session.get('user_type') != 'customer':
        messages.error(request, 'You must be logged in as a customer.')
        return redirect('home')
    
    notification = get_object_or_404(Notification, id=notification_id)
    user = Accounts.objects.get(id=request.session['user_id'])
    
    if notification.customer != user:
        messages.error(request, 'You do not have permission to modify this notification.')
        return redirect('messages:notifications')
    
    notification.is_read = True
    notification.save()
    
    return redirect('messages:notifications')
