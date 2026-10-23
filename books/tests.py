from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from categories.models import Category


class BookManagementTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fiction")
        self.book = Book.objects.create(
            title="A Test Novel",
            author="A. Writer",
            isbn="9780306406157",
            price=Decimal("14.95"),
            description="A sample book.",
            category=self.category,
            stock=4,
        )
        self.staff = User.objects.create_user(
            username="staff",
            password="StrongPass!123",
            is_staff=True,
        )

    def book_data(self, **overrides):
        data = {
            "title": "Another Book",
            "author": "B. Writer",
            "isbn": "9780131103627",
            "price": "20.50",
            "description": "Book description",
            "category": str(self.category.pk),
            "stock": "8",
        }
        data.update(overrides)
        return data

    def test_catalog_and_detail_are_public(self):
        response = self.client.get(reverse("books:list"))
        self.assertContains(response, "A Test Novel")

        response = self.client.get(reverse("books:detail", args=(self.book.pk,)))
        self.assertContains(response, "9780306406157")

    def test_catalog_search_price_filter_and_sort(self):
        response = self.client.get(
            reverse("books:list"),
            {"q": "writer", "min_price": "10", "max_price": "15", "sort": "-price"},
        )
        self.assertContains(response, "A Test Novel")
        self.assertNotContains(response, "Another title")

        response = self.client.get(reverse("books:list"), {"q": "A Test"})
        self.assertContains(response, "A Test Novel")

    def test_book_writes_require_staff(self):
        response = self.client.get(reverse("books:create"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('books:create')}")

        user = User.objects.create_user(username="reader", password="StrongPass!123")
        self.client.force_login(user)
        response = self.client.get(reverse("books:create"))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_update_and_delete_book(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("books:create"), self.book_data())
        created = Book.objects.get(title="Another Book")
        self.assertRedirects(response, reverse("books:list"))

        response = self.client.post(
            reverse("books:update", args=(created.pk,)),
            self.book_data(title="Updated Book"),
        )
        self.assertRedirects(response, reverse("books:detail", args=(created.pk,)))
        created.refresh_from_db()
        self.assertEqual(created.title, "Updated Book")

        response = self.client.post(reverse("books:delete", args=(created.pk,)))
        self.assertRedirects(response, reverse("books:list"))
        self.assertFalse(Book.objects.filter(pk=created.pk).exists())

    def test_invalid_isbn_is_rejected_by_book_form(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("books:create"),
            self.book_data(isbn="9780306406158"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid ISBN-10 or ISBN-13.")
        self.assertFalse(Book.objects.filter(title="Another Book").exists())

    def test_isbn_is_stored_in_canonical_format(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("books:create"),
            self.book_data(isbn="0-306-40615-2"),
        )

        self.assertRedirects(response, reverse("books:list"))
        self.assertTrue(Book.objects.filter(isbn="0306406152").exists())
