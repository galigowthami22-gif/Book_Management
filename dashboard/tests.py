from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from categories.models import Category
from orders.models import Order, OrderItem


class DashboardViewTests(TestCase):
    def test_dashboard_is_staff_only(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:index')}")

        reader = User.objects.create_user(username="reader", password="StrongPass!123")
        self.client.force_login(reader)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 403)

        staff = User.objects.create_user(username="staff", password="StrongPass!123", is_staff=True)
        self.client.force_login(staff)
        self.assertContains(self.client.get(reverse("dashboard:index")), "Dashboard")

    def test_dashboard_shows_sales_and_low_stock(self):
        staff = User.objects.create_user(username="sales-staff", password="test-password", is_staff=True)
        customer = User.objects.create_user(username="sales-reader", password="test-password")
        category = Category.objects.create(name="Dashboard fiction")
        book = Book.objects.create(
            title="Dashboard Book",
            author="Dashboard Author",
            isbn="9780306406157",
            price="12.50",
            category=category,
            stock=3,
        )
        order = Order.objects.create(
            user=customer, status=Order.Status.CONFIRMED, total="25.00"
        )
        OrderItem.objects.create(
            order=order, book=book, title=book.title, unit_price=book.price, quantity=2
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("dashboard:index"))

        self.assertContains(response, "Sales (confirmed onward)")
        self.assertContains(response, "$25.00")
        self.assertContains(response, "Dashboard Book")
        self.assertContains(response, "Order management")

    def test_staff_can_update_status_and_cancelled_order_restores_stock(self):
        staff = User.objects.create_user(username="order-staff", password="test-password", is_staff=True)
        customer = User.objects.create_user(username="order-reader", password="test-password")
        category = Category.objects.create(name="Order fiction")
        book = Book.objects.create(
            title="Order Dashboard Book",
            author="Order Author",
            isbn="9780131103627",
            price="10.00",
            category=category,
            stock=1,
        )
        order = Order.objects.create(user=customer, total="20.00")
        OrderItem.objects.create(
            order=order, book=book, title=book.title, unit_price=book.price, quantity=2
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("dashboard:order-status", args=(order.pk,)),
            {"status": Order.Status.CONFIRMED},
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

        response = self.client.post(
            reverse("dashboard:order-status", args=(order.pk,)),
            {"status": Order.Status.CANCELLED},
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        order.refresh_from_db()
        book.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(book.stock, 3)
        self.client.post(
            reverse("dashboard:order-status", args=(order.pk,)),
            {"status": Order.Status.CANCELLED},
        )
        book.refresh_from_db()
        self.assertEqual(book.stock, 3)

        shipped_order = Order.objects.create(user=customer, status=Order.Status.SHIPPED)
        response = self.client.post(
            reverse("dashboard:order-status", args=(shipped_order.pk,)),
            {"status": Order.Status.CANCELLED},
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        shipped_order.refresh_from_db()
        self.assertEqual(shipped_order.status, Order.Status.SHIPPED)

    def test_order_status_update_rejects_non_staff_and_invalid_status(self):
        customer = User.objects.create_user(username="status-reader", password="test-password")
        order = Order.objects.create(user=customer)
        self.client.force_login(customer)
        response = self.client.post(
            reverse("dashboard:order-status", args=(order.pk,)),
            {"status": Order.Status.CONFIRMED},
        )
        self.assertEqual(response.status_code, 403)

        staff = User.objects.create_user(username="status-staff", password="test-password", is_staff=True)
        self.client.force_login(staff)
        response = self.client.post(
            reverse("dashboard:order-status", args=(order.pk,)), {"status": "invalid"}
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
