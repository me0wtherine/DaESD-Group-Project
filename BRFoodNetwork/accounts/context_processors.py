from accounts.models import Accounts, Producers


def user_context(request):
    """Add logged-in user information to template context"""
    context = {
        'user_name': None,
        'user_type': None,
    }
    
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        user_type = request.session.get('user_type', 'customer')
        
        try:
            if user_type == 'customer':
                user = Accounts.objects.get(id=user_id)
                context['user_name'] = user.name
            elif user_type == 'producer':
                producer = Producers.objects.get(id=user_id)
                context['user_name'] = producer.business_name
            context['user_type'] = user_type
        except (Accounts.DoesNotExist, Producers.DoesNotExist):
            # Clear invalid session
            request.session.flush()
    
    return context
