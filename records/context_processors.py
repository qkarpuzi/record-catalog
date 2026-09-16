def cart(request):
    session_cart = request.session.get("cart", {})
    return {"cart_count": sum(session_cart.values())}
