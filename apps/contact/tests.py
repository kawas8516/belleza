from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class ContactSubmitTests(TestCase):
    def test_valid_message_saved(self):
        response = self.client.post(
            reverse("contact:submit"),
            {"name": "Asha", "phone": "+919876543210", "message": "Do you do keratin?"},
            follow=True,
        )
        self.assertRedirects(response, reverse("core:home") + "#form-loc")
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertContains(response, "get back to you soon")

    def test_invalid_phone_not_saved(self):
        response = self.client.post(
            reverse("contact:submit"),
            {"name": "Asha", "phone": "12ab", "message": "Hi"},
            follow=True,
        )
        self.assertFalse(ContactMessage.objects.exists())
        self.assertContains(response, "wasn&#x27;t sent")

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse("contact:submit")).status_code, 405)
