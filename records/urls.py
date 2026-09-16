from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "records"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),

    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<slug:slug>/", views.cart_add, name="cart_add"),
    path("cart/remove/<slug:slug>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),

    path("accounts/login/", auth_views.LoginView.as_view(template_name="records/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", views.register, name="register"),
    path("account/", views.account, name="account"),

    path("contact/", views.contact, name="contact"),
]
