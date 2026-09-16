from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )

    category_slug = request.GET.get("category", "").strip()
    if category_slug:
        products = products.filter(category__slug=category_slug)

    sort = request.GET.get("sort", "-created_at")
    allowed_sorts = {
        "price", "-price",
        "name", "-name",
        "created_at", "-created_at",
    }
    if sort not in allowed_sorts:
        sort = "-created_at"
    products = products.order_by(sort)

    paginator = Paginator(products, 24)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "query": query,
        "selected_category": category_slug,
        "sort": sort,
    }
    return render(request, "records/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        slug=slug,
        is_active=True,
    )

    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .select_related("category")[:4]
    )

    context = {
        "product": product,
        "related_products": related_products,
    }
    return render(request, "records/product_detail.html", context)


def home(request):
    featured_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("-created_at")[:8]
    )
    categories = Category.objects.all()[:6]
    return render(request, "records/home.html", {
        "featured_products": featured_products,
        "categories": categories,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True).select_related("category")

    sort = request.GET.get("sort", "-created_at")
    allowed_sorts = {
        "price", "-price",
        "name", "-name",
        "created_at", "-created_at",
    }
    if sort not in allowed_sorts:
        sort = "-created_at"
    products = products.order_by(sort)

    paginator = Paginator(products, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "page_obj": page_obj,
        "sort": sort,
    }
    return render(request, "records/category_detail.html", context)


def _cart_items(request):
    cart = request.session.get("cart", {})
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids).select_related("category")
    items = []
    total = Decimal("0.00")
    for product in products:
        quantity = cart.get(str(product.id), 0)
        subtotal = product.price * quantity
        total += subtotal
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
    return items, total


def cart_view(request):
    items, total = _cart_items(request)
    return render(request, "records/cart.html", {"items": items, "total": total})


def cart_add(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    cart = request.session.get("cart", {})
    key = str(product.id)
    cart[key] = cart.get(key, 0) + 1
    request.session["cart"] = cart
    messages.success(request, f"Added “{product.name}” to your cart.")
    return redirect("records:cart")


def cart_remove(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = request.session.get("cart", {})
    cart.pop(str(product.id), None)
    request.session["cart"] = cart
    return redirect("records:cart")


def checkout(request):
    items, total = _cart_items(request)

    if request.method == "POST" and items:
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        if name and email and address:
            request.session["cart"] = {}
            messages.success(
                request,
                f"Thanks {name}! Your order has been placed — a confirmation was sent to {email}.",
            )
            return redirect("records:home")
        messages.error(request, "Please fill in every field to complete your order.")

    return render(request, "records/checkout.html", {"items": items, "total": total})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("records:account")
    else:
        form = UserCreationForm()
    return render(request, "records/register.html", {"form": form})


@login_required
def account(request):
    return render(request, "records/account.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            messages.success(request, "Thanks for reaching out — we'll get back to you soon.")
            return redirect("records:contact")
        messages.error(request, "Please fill in every field before sending.")
    return render(request, "records/contact.html")
