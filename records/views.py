from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

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