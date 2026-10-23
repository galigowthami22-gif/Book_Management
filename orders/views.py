from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from cart.models import Cart
from books.models import Book
from orders.models import Order, OrderItem


class InsufficientStockError(Exception):
    pass


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related("book"))
    if request.method == "GET":
        return render(request, "orders/checkout.html", {"cart": cart, "items": items})
    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:detail")

    try:
        with transaction.atomic():
            locked_items = list(
                cart.items.select_for_update().select_related("book").order_by("book_id")
            )
            if not locked_items:
                messages.error(request, "Your cart is empty.")
                return redirect("cart:detail")

            for item in locked_items:
                updated = Book.objects.filter(
                    pk=item.book_id, stock__gte=item.quantity
                ).update(stock=F("stock") - item.quantity)
                if updated != 1:
                    raise InsufficientStockError(f"Not enough stock for {item.book.title}.")

            order = Order.objects.create(user=request.user)
            total = 0
            for item in locked_items:
                OrderItem.objects.create(
                    order=order,
                    book=item.book,
                    title=item.book.title,
                    unit_price=item.book.price,
                    quantity=item.quantity,
                )
                total += item.book.price * item.quantity
            order.total = total
            order.save(update_fields=("total",))
            cart.items.all().delete()
    except InsufficientStockError as error:
        messages.error(request, str(error))
        return redirect("cart:detail")

    messages.success(request, f"Order #{order.pk} placed successfully.")
    return redirect("orders:list")
