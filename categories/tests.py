from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from categories.models import Category


class CategoryManagementTests(TestCase):
    def test_staff_can_create_and_edit_categories(self):
        staff = User.objects.create_user(username="staff", password="StrongPass!123", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            reverse("categories:create"),
            {"name": "Science", "description": "Science books", "is_active": "on"},
        )
        category = Category.objects.get(name="Science")
        self.assertRedirects(response, reverse("categories:list"))

        response = self.client.post(
            reverse("categories:update", args=(category.pk,)),
            {"name": "Science Fiction", "description": "", "is_active": "on"},
        )
        self.assertRedirects(response, reverse("categories:list"))
        self.assertTrue(Category.objects.filter(pk=category.pk, name="Science Fiction").exists())

    def test_category_with_books_cannot_be_deleted(self):
        staff = User.objects.create_user(username="staff", password="StrongPass!123", is_staff=True)
        category = Category.objects.create(name="Fiction")
        Book.objects.create(
            title="A Test Novel",
            author="A. Writer",
            isbn="9780306406157",
            price="14.95",
            category=category,
        )
        self.client.force_login(staff)

        response = self.client.post(reverse("categories:delete", args=(category.pk,)))

        self.assertRedirects(response, reverse("categories:list"))
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
