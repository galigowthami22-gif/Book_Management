from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from decimal import Decimal
from books.models import Book
from cart.models import Cart, CartItem
from categories.models import Category
from orders.models import Order, OrderItem


class OrderViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="order-reader", password="test-password")
        category = Category.objects.create(name="Order fiction")
        self.book = Book.objects.create(
            title="Order Test Book",
            author="Order Author",
            isbn="9780306406157",
            price=Decimal("14.95"),
            category=category,
            stock=4,
        )

    def test_order_list_requires_login_and_renders_empty_state(self):
        response = self.client.get(reverse("orders:list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('orders:list')}")

        user = User.objects.create_user(username="reader", password="StrongPass!123")
        self.client.force_login(user)
        response = self.client.get(reverse("orders:list"))

        self.assertContains(response, "You have not placed any orders.")

    def test_checkout_creates_order_and_decrements_stock(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=2)
        self.client.force_login(self.user)

        response = self.client.get(reverse("orders:checkout"))
        self.assertContains(response, "Place order")

        response = self.client.post(reverse("orders:checkout"))

        self.assertRedirects(response, reverse("orders:list"))
        order = Order.objects.get(user=self.user)
        item = OrderItem.objects.get(order=order)
        self.book.refresh_from_db()
        self.assertEqual(order.total, Decimal("29.90"))
        self.assertEqual(item.title, "Order Test Book")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(self.book.stock, 2)
        self.assertFalse(cart.items.exists())

    def test_checkout_rejects_insufficient_stock_without_partial_order(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, book=self.book, quantity=5)
        self.client.force_login(self.user)

        response = self.client.post(reverse("orders:checkout"))

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 4)
        self.assertTrue(cart.items.exists())

    def test_registered_customer_can_search_checkout_and_view_order_history(self):
        registration = self.client.post(
            reverse("accounts:register"),
            {
                "username": "workflow-reader",
                "first_name": "Workflow",
                "last_name": "Reader",
                "email": "workflow@example.com",
                "password1": "StrongPass!123",
                "password2": "StrongPass!123",
            },
        )
        self.assertRedirects(registration, reverse("books:list"))
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
        self.client.post(reverse("accounts:logout"))
        login = self.client.post(
            reverse("accounts:login"),
            {"username": "workflow-reader", "password": "StrongPass!123"},
        )
        self.assertRedirects(login, reverse("books:list"))

        search = self.client.get(reverse("books:list"), {"q": "Order Author"})
        self.assertContains(search, "Order Test Book")
        add = self.client.post(reverse("cart:add", args=(self.book.pk,)), {"quantity": 2})
        self.assertRedirects(add, reverse("cart:detail"))
        checkout = self.client.post(reverse("orders:checkout"))
        self.assertRedirects(checkout, reverse("orders:list"))

        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 2)
        order = Order.objects.get(user__username="workflow-reader")
        self.assertContains(self.client.get(reverse("orders:list")), "Order Test Book")
        self.assertEqual(order.total, Decimal("29.90"))
