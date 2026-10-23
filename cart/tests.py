from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from decimal import Decimal
from books.models import Book
from cart.models import Cart, CartItem
from categories.models import Category


class CartViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cart-reader", password="test-password")
        category = Category.objects.create(name="Cart fiction")
        self.book = Book.objects.create(
            title="Cart Test Book",
            author="Cart Author",
            isbn="9780306406157",
            price=Decimal("14.95"),
            category=category,
            stock=4,
        )

    def test_cart_requires_login_and_renders_empty_cart(self):
        response = self.client.get(reverse("cart:detail"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('cart:detail')}")

        user = User.objects.create_user(username="reader", password="StrongPass!123")
        self.client.force_login(user)
        response = self.client.get(reverse("cart:detail"))

        self.assertContains(response, "Your cart is empty.")

    def test_user_can_add_update_and_remove_cart_items(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("cart:add", args=(self.book.pk,)), {"quantity": 2})
        self.assertRedirects(response, reverse("cart:detail"))
        cart_item = CartItem.objects.get(cart__user=self.user, book=self.book)
        self.assertEqual(cart_item.quantity, 2)

        response = self.client.post(
            reverse("cart:update", args=(cart_item.pk,)), {"quantity": 3}
        )
        self.assertRedirects(response, reverse("cart:detail"))
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)
        self.assertContains(self.client.get(reverse("cart:detail")), "$44.85")

        response = self.client.post(reverse("cart:remove", args=(cart_item.pk,)))
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertFalse(CartItem.objects.filter(pk=cart_item.pk).exists())

    def test_cart_rejects_quantities_above_stock(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("cart:add", args=(self.book.pk,)), {"quantity": 5})
        self.assertRedirects(response, reverse("books:detail", args=(self.book.pk,)))
        self.assertFalse(Cart.objects.filter(user=self.user, items__book=self.book).exists())
