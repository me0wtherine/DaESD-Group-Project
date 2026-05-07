from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages

from django.contrib.auth.hashers import make_password, check_password

from django.http import HttpResponse

from datetime import datetime, timedelta

import csv



from .forms import AdminSignupForm, AdminLoginForm, SignupForm, ProducerSignupForm, CustomerLoginForm, ProducerLoginForm

from .models import Accounts, Producers, Admins

from .geocoding import geocode_address, is_within_bristol_radius

from orders.models import Orders, OrderItem

from cart.models import Cart, CartItem



def account_type_signup(request):

    """Choose between customer or producer sign-up."""

    return render(request, 'registration/account_type_signup.html')





def account_type_login(request):

    """Choose between customer or producer log-in."""

    return render(request, 'registration/account_type_login.html')





def signup_view(request):

    """Customer account registration."""

    if request.method == 'POST':

        form = SignupForm(request.POST)

        if form.is_valid():

            account = form.save(commit=False)

            account.password = make_password(form.cleaned_data['password'])



            # Geocode address and enforce 20-mile radius

            try:

                lat, lng = geocode_address(account.address, account.postal_code)

            except Exception as e:

                print("GEOCODE ERROR:", e)

                messages.error(request, 'Address verification unavailable.')

                return render(request, 'registration/signup.html', {'form': form})

            if lat is None or lng is None:

                messages.error(request, 'We could not verify your address. Please enter a valid UK address and postal code.')

                return render(request, 'registration/signup.html', {'form': form})



            if not is_within_bristol_radius(lat, lng):

                messages.error(request, 'Sorry, the Bristol Regional Food Network only serves customers within a 20-mile radius of Bristol city centre.')

                return render(request, 'registration/signup.html', {'form': form})



            account.latitude = lat

            account.longitude = lng

            account.save()

            messages.success(request, 'Account created successfully!')

            return redirect('customer_login')

    else:

        form = SignupForm()



    return render(request, 'registration/signup.html', {'form': form})





def producer_signup_view(request):

    """Producer account registration."""

    if request.method == 'POST':

        form = ProducerSignupForm(request.POST)

        if form.is_valid():

            producer = form.save(commit=False)

            producer.password = make_password(form.cleaned_data['password'])



            # Geocode address for map pin and enforce 20-mile radius

            lat, lng = geocode_address(producer.address, producer.postal_code)

            if lat is None or lng is None:

                messages.error(request, 'We could not verify your address. Please enter a valid UK address and postal code.')

                return render(request, 'registration/producersignup.html', {'form': form})



            if not is_within_bristol_radius(lat, lng):

                messages.error(request, 'Sorry, the Bristol Regional Food Network only accepts producers within a 20-mile radius of Bristol city centre.')

                return render(request, 'registration/producersignup.html', {'form': form})



            producer.latitude = lat

            producer.longitude = lng

            producer.save()

            messages.success(request, 'Producer account created successfully!')

            return redirect('producer_login')

    else:

        form = ProducerSignupForm()



    return render(request, 'registration/producersignup.html', {'form': form})





def customer_login(request):

    """Customer log-in. Also accepts admin credentials and redirects to admin dashboard."""

    if request.method == 'POST':

        form = CustomerLoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            password = form.cleaned_data['password']



            # Check admin accounts first

            try:

                admin = Admins.objects.get(email=email)

                if check_password(password, admin.password):

                    request.session['user_id'] = admin.id

                    request.session['user_type'] = 'admin'

                    request.session['user_name'] = admin.name

                    return redirect('admin_dashboard')

                else:

                    messages.error(request, 'Invalid email or password')

                    return render(request, 'registration/customer_login.html', {'form': form})

            except Admins.DoesNotExist:

                pass



            # Fall through to regular customer check

            try:

                user = Accounts.objects.get(email=email)

                if check_password(password, user.password):

                    request.session['user_id'] = user.id

                    request.session['user_type'] = 'customer'

                    request.session['user_name'] = user.name

                    return redirect('home')

                else:

                    messages.error(request, 'Invalid email or password')

            except Accounts.DoesNotExist:

                messages.error(request, 'Invalid email or password')

    else:

        form = CustomerLoginForm()



    return render(request, 'registration/customer_login.html', {'form': form})





def producer_login(request):

    """Producer log-in with email and password."""

    if request.method == 'POST':

        form = ProducerLoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            password = form.cleaned_data['password']

            try:

                producer = Producers.objects.get(email=email)

                if check_password(password, producer.password):

                    request.session['user_id'] = producer.id

                    request.session['user_type'] = 'producer'

                    request.session['user_name'] = producer.business_name

                    return redirect('home')

                else:

                    messages.error(request, 'Invalid email or password')

            except Producers.DoesNotExist:

                messages.error(request, 'Invalid email or password')

    else:

        form = ProducerLoginForm()



    return render(request, 'registration/producer_login.html', {'form': form})





def order_history(request):

    """Show logged-in customers their past orders."""

    user_id = request.session.get('user_id')

    user_type = request.session.get('user_type')



    if not user_id or user_type != 'customer':

        messages.error(request, 'You must be logged in as a customer to view your order history.')

        return redirect('customer_login')



    customer = Accounts.objects.filter(id=user_id).first()

    if not customer:

        request.session.flush()

        messages.error(request, 'Please log in again.')

        return redirect('customer_login')



    orders = Orders.objects.filter(user=customer).order_by('-order_date')



    return render(request, 'accounts/order_history.html', {

        'customer': customer,

        'orders': orders,

    })



def reorder(request, order_id):

    user_id = request.session.get('user_id')

    user_type = request.session.get('user_type')



    if not user_id or user_type != 'customer':

        messages.error(request, 'You must be logged in as a customer to reorder.')

        return redirect('customer_login')

    

    customer = Accounts.objects.filter(id=user_id).first()

    if not customer:

        request.session.flush()

        return redirect('customer_login')

    order = get_object_or_404(Orders, id=order_id, user=customer)



    cart, _ = Cart.objects.get_or_create(user=customer)



    for item in order.items.all():

        cart_item, created = CartItem.objects.get_or_create(

            cart=cart,

            product=item.product,

            defaults={'quantity': item.quantity}



        )



        if not created:

            cart_item.quantity += item.quantity

            cart_item.save()

        

        messages.success(request, 'Items from this order have been added to your basket.')

        return redirect('cart:detail')





def logout_view(request):

    """Clear the session and redirect to the homepage."""

    request.session.flush()

    return redirect('home')



def admin_home(request):

    """Admin dashboard showing overview of producers, customers, and orders."""

    user_id = request.session.get('user_id')

    user_type = request.session.get('user_type')

    user_name = request.session.get('user_name')



    if not user_id or user_type != 'admin':

        messages.error(request, 'You must be logged in as an admin to access the admin dashboard.')

        return redirect('customer_login')



    producers = Producers.objects.all().order_by('business_name')

    customers = Accounts.objects.all().order_by('name')

    admins = Admins.objects.all().order_by('name')



    recent_orders = Orders.objects.select_related('user').order_by('-order_date')[:10]



    return render(request, 'admin/admin_home.html', {

        'user_name': user_name,

        'producers': producers,

        'customers': customers,

        'admins': admins,

        'recent_orders': recent_orders,

        'producer_count': producers.count(),

        'customer_count': customers.count(),

        'admin_count': admins.count(),

        'order_count': Orders.objects.count(),

        'active_producer_count': producers.filter(is_active=True).count(),

    })



def admin_edit_customer(request, customer_id):

    """Admin: view and edit a customer account, including their orders."""

    if request.session.get('user_type') != 'admin':

        return redirect('customer_login')



    customer = get_object_or_404(Accounts, id=customer_id)

    orders = Orders.objects.filter(user=customer).prefetch_related('items__product').order_by('-order_date')

    error = None

    success = None



    if request.method == 'POST':

        action = request.POST.get('action')



        if action == 'save_details':

            name = request.POST.get('name', '').strip()

            email = request.POST.get('email', '').strip()

            postal_code = request.POST.get('postal_code', '').strip()

            customer_type = request.POST.get('customer_type', '').strip()

            new_password = request.POST.get('new_password', '').strip()

            address = request.POST.get('address', '').strip()

            phone_number = request.POST.get('phone_number', '').strip()



            if not name or not email or not postal_code or not customer_type:

                error = 'Name, email, postcode and account type are required.'

            elif Accounts.objects.exclude(id=customer_id).filter(email=email).exists():

                error = 'That email is already in use by another account.'

            else:

                # Re-geocode and enforce 20-mile Bristol radius whenever address/postcode changes

                lat, lng = geocode_address(address, postal_code)

                if lat is None or lng is None:

                    error = 'Could not verify that address. Please enter a valid UK address and postcode.'

                elif not is_within_bristol_radius(lat, lng):

                    error = 'That address is outside the 20-mile Bristol service area (straight-line distance from city centre).'

                else:

                    customer.name = name

                    customer.email = email

                    customer.postal_code = postal_code

                    customer.customer_type = customer_type

                    customer.address = address

                    customer.phone_number = phone_number

                    customer.latitude = lat

                    customer.longitude = lng

                    if new_password:

                        customer.password = make_password(new_password)

                    customer.save()

                    success = 'Customer details updated successfully.'



        elif action == 'promote_admin':

            # Convert this customer into an admin account.

            if Admins.objects.filter(email=customer.email).exists():

                error = 'An admin with that email already exists.'

            else:

                Admins.objects.create(

                    name=customer.name,

                    email=customer.email,

                    password=customer.password,  # already hashed

                )

                customer.delete()

                messages.success(request, f'{customer.name} has been promoted to admin.')

                return redirect('admin_dashboard')



        elif action == 'delete_account':

            customer.delete()

            return redirect('admin_dashboard')



        elif action == 'update_order_status':

            order_id = request.POST.get('order_id')

            new_status = request.POST.get('order_status')

            order = get_object_or_404(Orders, id=order_id, user=customer)

            valid_statuses = [c[0] for c in Orders.ORDER_STATUS_CHOICES]

            if new_status in valid_statuses:

                order.order_status = new_status

                order.save()

                success = f'Order #{order_id} status updated.'



    return render(request, 'admin/admin_edit_customer.html', {

        'customer': customer,

        'orders': orders,

        'customer_type_choices': Accounts.CUSTOMER_TYPE_CHOICES,

        'order_status_choices': Orders.ORDER_STATUS_CHOICES,

        'error': error,

        'success': success,

    })





def admin_edit_producer(request, producer_id):

    """Admin: view and edit a producer account, including their orders."""

    if request.session.get('user_type') != 'admin':

        return redirect('customer_login')



    producer = get_object_or_404(Producers, id=producer_id)

    # Orders are linked to customers; show orders containing this producer's products

    order_ids = OrderItem.objects.filter(

        product__producer=producer

    ).values_list('order_id', flat=True).distinct()

    orders = Orders.objects.filter(id__in=order_ids).select_related('user').prefetch_related('items__product').order_by('-order_date')

    error = None

    success = None



    if request.method == 'POST':

        action = request.POST.get('action')



        if action == 'save_details':

            business_name = request.POST.get('business_name', '').strip()

            email = request.POST.get('email', '').strip()

            postal_code = request.POST.get('postal_code', '').strip()

            phone_number = request.POST.get('phone_number', '').strip()

            new_password = request.POST.get('new_password', '').strip()

            is_active = request.POST.get('is_active') == 'on'

            address = request.POST.get('address', '').strip()

            description = request.POST.get('description', '').strip()



            if not business_name or not email or not postal_code:

                error = 'Business name, email and postcode are required.'

            elif Producers.objects.exclude(id=producer_id).filter(email=email).exists():

                error = 'That email is already in use by another producer.'

            else:

                # Re-geocode and enforce 20-mile Bristol radius whenever address/postcode changes

                lat, lng = geocode_address(address, postal_code)

                if lat is None or lng is None:

                    error = 'Could not verify that address. Please enter a valid UK address and postcode.'

                elif not is_within_bristol_radius(lat, lng):

                    error = 'That address is outside the 20-mile Bristol service area (straight-line distance from city centre).'

                else:

                    producer.business_name = business_name

                    producer.email = email

                    producer.postal_code = postal_code

                    producer.phone_number = phone_number

                    producer.address = address

                    producer.description = description

                    producer.is_active = is_active

                    producer.latitude = lat

                    producer.longitude = lng

                    if new_password:

                        producer.password = make_password(new_password)

                    producer.save()

                    success = 'Producer details updated successfully.'



        elif action == 'promote_admin':

            # Convert this producer into an admin account.

            if Admins.objects.filter(email=producer.email).exists():

                error = 'An admin with that email already exists.'

            else:

                Admins.objects.create(

                    name=producer.business_name,

                    email=producer.email,

                    password=producer.password,  # already hashed

                )

                producer.delete()

                messages.success(request, f'{producer.business_name} has been promoted to admin.')

                return redirect('admin_dashboard')



        elif action == 'delete_account':

            producer.delete()

            return redirect('admin_dashboard')



        elif action == 'update_order_status':

            order_id = request.POST.get('order_id')

            new_status = request.POST.get('order_status')

            order = get_object_or_404(Orders, id=order_id)

            valid_statuses = [c[0] for c in Orders.ORDER_STATUS_CHOICES]

            if new_status in valid_statuses:

                order.order_status = new_status

                order.save()

                success = f'Order #{order_id} status updated.'



    return render(request, 'admin/admin_edit_producer.html', {

        'producer': producer,

        'orders': orders,

        'order_status_choices': Orders.ORDER_STATUS_CHOICES,

        'error': error,

        'success': success,

    })




def admin_edit_admin(request, admin_id):
    """Admin: view and edit an admin account."""
    if request.session.get('user_type') != 'admin':
        return redirect('customer_login')

    admin = get_object_or_404(Admins, id=admin_id)
    error = None
    success = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_details':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            new_password = request.POST.get('new_password', '').strip()

            if not name or not email:
                error = 'Name and email are required.'
            elif Admins.objects.exclude(id=admin_id).filter(email=email).exists():
                error = 'That email is already in use by another admin.'
            else:
                admin.name = name
                admin.email = email
                if new_password:
                    admin.password = make_password(new_password)
                admin.save()
                success = 'Admin details updated successfully.'

        elif action == 'delete_account':
            # Prevent admin from deleting themselves
            if request.session.get('user_id') == admin.id:
                error = 'You cannot delete your own admin account while logged in.'
            else:
                admin.delete()
                return redirect('admin_dashboard')

    return render(request, 'admin/admin_edit_admin.html', {
        'admin': admin,
        'error': error,
        'success': success,
        'is_self': request.session.get('user_id') == admin.id,
    })


def create_admin_account(request):

    """Utility function to create an admin account."""

    if request.method == 'POST':

        form = AdminSignupForm(request.POST)

        if form.is_valid():

            admin = form.save(commit=False)

            admin.password = make_password(form.cleaned_data['password'])

            admin.save()

            messages.success(request, 'Admin account created successfully!')

            return redirect('admin_dashboard')

    else:

        form = AdminSignupForm()



    return render(request, 'admin/admin_account_create.html', {'form': form})

    

def admin_login(request):

    """Admin log-in with email and password."""

    if request.method == 'POST':

        form = AdminLoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            password = form.cleaned_data['password']

            try:

                admin = Admins.objects.get(email=email)

                if check_password(password, admin.password):

                    request.session['user_id'] = admin.id

                    request.session['user_type'] = 'admin'

                    request.session['user_name'] = admin.name

                    print(request.session.get('user_type'))

                    messages.success(request, f'Welcome back, {admin.name}!')

                    return redirect('admin_dashboard')

                else:

                    messages.error(request, 'Invalid email or password')

            except Admins.DoesNotExist:

                messages.error(request, 'Invalid email or password')

    else:

        form = AdminLoginForm()



    return render(request, 'admin/admin_login.html', {'form': form})
def admin_commission_report(request):
    """Admin financial report: 5% network commission across all orders (TC-025)."""
    if request.session.get('user_type') != 'admin':
        return redirect('customer_login')

    from payments.models import Payments
    from decimal import Decimal

    # Date range filter (defaults to last 14 days)
    end_str = request.GET.get('end_date')
    start_str = request.GET.get('start_date')
    today = datetime.now().date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else today
    start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else (end_date - timedelta(days=14))

    payments = (
        Payments.objects
        .select_related('order', 'order__user', 'producer')
        .filter(order__order_date__date__gte=start_date,
                order__order_date__date__lte=end_date)
        .order_by('-order__order_date')
    )

    total_order_value = sum((p.network_commission + p.producer_payment for p in payments), Decimal('0.00'))
    total_commission = sum((p.network_commission for p in payments), Decimal('0.00'))
    total_producer_payouts = sum((p.producer_payment for p in payments), Decimal('0.00'))

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="commission_report_{start_date}_to_{end_date}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Order Date', 'Customer', 'Producer',
            'Producer Payment (95%)', 'Network Commission (5%)', 'Order Subtotal'
        ])
        for p in payments:
            writer.writerow([
                p.order.id,
                p.order.order_date.strftime('%Y-%m-%d'),
                p.order.user.name if p.order.user else '',
                p.producer.business_name,
                f'{p.producer_payment:.2f}',
                f'{p.network_commission:.2f}',
                f'{(p.network_commission + p.producer_payment):.2f}',
            ])
        writer.writerow([])
        writer.writerow(['', '', '', 'TOTALS',
                         f'{total_producer_payouts:.2f}',
                         f'{total_commission:.2f}',
                         f'{total_order_value:.2f}'])
        return response

    # Group by producer for summary
    producer_summary = {}
    for p in payments:
        pid = p.producer.id
        if pid not in producer_summary:
            producer_summary[pid] = {
                'producer': p.producer,
                'order_count': 0,
                'total_payment': Decimal('0.00'),
                'total_commission': Decimal('0.00'),
                'total_value': Decimal('0.00'),
            }
        producer_summary[pid]['order_count'] += 1
        producer_summary[pid]['total_payment'] += p.producer_payment
        producer_summary[pid]['total_commission'] += p.network_commission
        producer_summary[pid]['total_value'] += (p.network_commission + p.producer_payment)

    return render(request, 'admin/admin_commission_report.html', {
        'payments': payments,
        'producer_summary': producer_summary.values(),
        'start_date': start_date,
        'end_date': end_date,
        'total_order_value': total_order_value,
        'total_commission': total_commission,
        'total_producer_payouts': total_producer_payouts,
        'order_count': payments.count(),
    })


def order_receipt(request, order_id):
    """Printable order receipt — accessible to the order's owner or an admin (TC-021)."""
    order = get_object_or_404(
        Orders.objects.select_related('user').prefetch_related('items__product__producer'),
        id=order_id,
    )

    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if user_type == 'admin':
        pass  # admins can view any receipt
    elif user_type == 'customer' and order.user_id == user_id:
        pass
    else:
        messages.error(request, 'You do not have permission to view this receipt.')
        return redirect('customer_login')

    # Group items by producer for multi-vendor breakdown
    from decimal import Decimal
    producers_breakdown = {}
    for item in order.items.all():
        pid = item.product.producer.id
        if pid not in producers_breakdown:
            producers_breakdown[pid] = {
                'producer': item.product.producer,
                'items': [],
                'subtotal': Decimal('0.00'),
            }
        line_total = item.price * item.quantity
        producers_breakdown[pid]['items'].append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.price,
            'line_total': line_total,
        })
        producers_breakdown[pid]['subtotal'] += line_total

    return render(request, 'accounts/order_receipt.html', {
        'order': order,
        'producers_breakdown': producers_breakdown.values(),
    })

