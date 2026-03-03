from django.urls import path
from . import views

urlpatterns = [
    path("account-type/signup/", views.account_type_signup, name="account_type_signup"),
    path("account-type/login/", views.account_type_login, name="account_type_login"),
    path("signup/", views.SignUpView, name="signup"), 
    path("psignup/", views.ProducerSignUpView, name="producersignup"),
    path("login/customer/", views.customer_login, name="customer_login"),
    path("login/producer/", views.producer_login, name="producer_login"),
    path("logout/", views.logout_view, name="logout"),
]