from django.conf import settings
from django.db import models
from decimal import Decimal

from books.models import Book


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user}"

    @property
    def subtotal(self):
        return sum((item.subtotal for item in self.items.all()), start=Decimal("0.00"))

    @property
    def total(self):
        return self.subtotal


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("cart", "book"), name="unique_book_per_cart")
        ]

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    @property
    def subtotal(self):
        return self.book.price * self.quantity
