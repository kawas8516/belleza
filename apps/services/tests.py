from django.test import TestCase
from django.urls import reverse

from .models import Category, Service, Stylist


class SeedDataTests(TestCase):
    def test_catalogue_seeded(self):
        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Service.objects.count(), 25)
        self.assertEqual(Stylist.objects.count(), 3)
        self.assertEqual(
            [c.display_title for c in Category.objects.featured()],
            ["Hair Styling", "Makeup Services", "Nail Art"],
        )


class ServiceListViewTests(TestCase):
    def test_renders_featured_cards(self):
        response = self.client.get(reverse("services:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="service-item"', count=3)
        self.assertContains(response, "Nail Art")
        self.assertContains(response, reverse("bookings:create"))

    def test_unfeatured_category_hidden(self):
        Category.objects.filter(slug="nails").update(is_featured=False)
        response = self.client.get(reverse("services:list"))
        self.assertContains(response, 'class="service-item"', count=2)
