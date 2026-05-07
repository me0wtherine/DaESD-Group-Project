from django.urls import path
from . import views

urlpatterns = [
    path('account-type/signup/', views.account_type_signup, name='account_type_signup'),
    path('account-type/login/', views.account_type_login, name='account_type_login'),
    path('signup/', views.signup_view, name='signup'),
    path('psignup/', views.producer_signup_view, name='producersignup'),
    path('login/customer/', views.customer_login, name='customer_login'),
    path('login/producer/', views.producer_login, name='producer_login'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/reorder/<int:order_id>/', views.reorder, name='reorder'),
    path('orders/receipt/<int:order_id>/', views.order_receipt, name='order_receipt'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', views.admin_home, name='admin_dashboard'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/create_admin/', views.create_admin_account, name='create_admin_account'),
    path('admin/customer/<int:customer_id>/', views.admin_edit_customer, name='admin_edit_customer'),
    path('admin/producer/<int:producer_id>/', views.admin_edit_producer, name='admin_edit_producer'),
    path('admin/admin/<int:admin_id>/', views.admin_edit_admin, name='admin_edit_admin'),
    path('admin/commission/', views.admin_commission_report, name='admin_commission_report'),
]
