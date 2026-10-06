from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="Asha@Example.com", password="s3cret-pass", full_name="Asha")
        self.assertEqual(user.email, "Asha@example.com")
        self.assertTrue(user.check_password("s3cret-pass"))
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="s3cret-pass", full_name="Admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthViewTests(TestCase):
    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "full_name": "Asha Patil",
                "email": "asha@example.com",
                "password1": "Belleza-2026!",
                "password2": "Belleza-2026!",
                "agree_terms": "on",
            },
        )
        self.assertRedirects(response, reverse("core:home"))
        user = User.objects.get(email="asha@example.com")
        self.assertEqual(user.full_name, "Asha Patil")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_requires_terms(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "full_name": "Asha",
                "email": "asha@example.com",
                "password1": "Belleza-2026!",
                "password2": "Belleza-2026!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertContains(response, "Terms of service to continue")

    def test_login_without_remember_me_expires_at_browser_close(self):
        User.objects.create_user(email="asha@example.com", password="Belleza-2026!", full_name="Asha")
        response = self.client.post(
            reverse("accounts:login"), {"username": "asha@example.com", "password": "Belleza-2026!"}
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_me_keeps_session(self):
        User.objects.create_user(email="asha@example.com", password="Belleza-2026!", full_name="Asha")
        self.client.post(
            reverse("accounts:login"),
            {"username": "asha@example.com", "password": "Belleza-2026!", "remember_me": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_next_redirect(self):
        User.objects.create_user(email="asha@example.com", password="Belleza-2026!", full_name="Asha")
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "asha@example.com", "password": "Belleza-2026!", "next": "/book/"},
        )
        self.assertRedirects(response, "/book/")

    def test_logout_is_post_only(self):
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
