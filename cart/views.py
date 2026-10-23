from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.models import Cart, CartItem
from books.models import Book


def _get_quantity(request):
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        return None
    return quantity if quantity > 0 else None


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("book").all()
    return render(request, "cart/cart_detail.html", {"cart": cart, "items": items})


@login_required
@require_POST
def add_to_cart(request, book_id):
    quantity = _get_quantity(request)
    book = get_object_or_404(Book, pk=book_id)
    if quantity is None:
        messages.error(request, "Enter a valid quantity greater than zero.")
        return redirect("books:detail", pk=book.pk)
    if quantity > book.stock:
        messages.error(request, "There is not enough stock for that quantity.")
        return redirect("books:detail", pk=book.pk)

    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        item = CartItem.objects.select_for_update().filter(cart=cart, book=book).first()
        if item is None:
            CartItem.objects.create(cart=cart, book=book, quantity=quantity)
        else:
            new_quantity = item.quantity + quantity
            if new_quantity > book.stock:
                messages.error(request, "There is not enough stock for that quantity.")
                return redirect("books:detail", pk=book.pk)
            item.quantity = new_quantity
            item.save(update_fields=("quantity",))

    messages.success(request, "Book added to your cart.")
    return redirect("cart:detail")


@login_required
@require_POST
def update_cart_item(request, item_id):
    quantity = _get_quantity(request)
    cart_item = get_object_or_404(
        CartItem.objects.select_related("book"), pk=item_id, cart__user=request.user
    )
    if quantity is None:
        messages.error(request, "Enter a valid quantity greater than zero.")
    elif quantity > cart_item.book.stock:
        messages.error(request, "There is not enough stock for that quantity.")
    else:
        cart_item.quantity = quantity
        cart_item.save(update_fields=("quantity",))
        messages.success(request, "Cart quantity updated.")
    return redirect("cart:detail")


@login_required
@require_POST
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Book removed from your cart.")
    return redirect("cart:detail")
