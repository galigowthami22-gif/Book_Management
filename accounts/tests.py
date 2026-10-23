from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile


class AccountViewTests(TestCase):
    def test_registration_creates_profile_and_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "reader",
                "first_name": "Read",
                "last_name": "Er",
                "email": "reader@example.com",
                "password1": "StrongPass!123",
                "password2": "StrongPass!123",
            },
        )

        self.assertRedirects(response, reverse("books:list"))
        user = User.objects.get(username="reader")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_requires_login_and_updates_user_and_profile(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

        user = User.objects.create_user(
            username="profile-reader",
            password="StrongPass!123",
            first_name="Old",
            last_name="Name",
            email="old@example.com",
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "New",
                "last_name": "Name",
                "email": "new@example.com",
                "phone": "555-0100",
                "address": "1 Main Street",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.profile.phone, "555-0100")

    def test_login_and_post_logout(self):
        User.objects.create_user(username="login-reader", password="StrongPass!123")
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login-reader", "password": "StrongPass!123"},
        )
        self.assertRedirects(response, reverse("books:list"))
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("books:list"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_page_does_not_echo_submitted_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "missing", "password": "SensitivePass!123"},
        )
        self.assertNotContains(response, "value=\"SensitivePass!123\"")
