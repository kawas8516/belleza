from decimal import Decimal
from unittest import mock

from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from .models import SiteSettings
from .templatetags.belleza import copyright_years, duration, rupees


class SiteSettingsTests(TestCase):
    def test_seeded_singleton(self):
        site = SiteSettings.load()
        self.assertEqual(site.pk, 1)
        self.assertEqual(site.hero_title, "Book your Styling Session on Tips")
        self.assertEqual(site.phone, "123-456-7890")
        self.assertEqual(site.about_text.count("\n\n"), 1)

    def test_save_always_uses_pk_1(self):
        SiteSettings(phone="999").save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().phone, "999")

    def test_footer_reflects_edits_on_every_page(self):
        site = SiteSettings.load()
        site.phone = "020-1234-5678"
        site.save()
        for name in ("core:home", "services:list", "core:contact"):
            with self.subTest(page=name):
                self.assertContains(self.client.get(reverse(name)), "020-1234-5678")

    def test_home_renders_copy_from_settings(self):
        site = SiteSettings.load()
        site.hero_title = "Fresh hero"
        site.about_text = "First para.\n\nSecond para."
        site.save()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "<h1>Fresh hero</h1>")
        self.assertContains(response, "<p>First para.</p>")
        self.assertContains(response, "<p>Second para.</p>")


class TemplateTagTests(TestCase):
    def test_copyright_years(self):
        with mock.patch("apps.core.templatetags.belleza.timezone.localdate") as today:
            today.return_value.year = 2026
            self.assertEqual(copyright_years(2023), "2023–2026")
            self.assertEqual(copyright_years(2026), "2026")

    def test_rupees(self):
        self.assertEqual(rupees(500), "₹500")
        self.assertEqual(rupees(1300), "₹1,300")
        self.assertEqual(rupees(12000), "₹12,000")
        self.assertEqual(rupees(150000), "₹1,50,000")
        self.assertEqual(rupees(Decimal("1300.00")), "₹1,300")
        self.assertEqual(rupees(Decimal("99.50")), "₹99.50")

    def test_duration(self):
        self.assertEqual(duration(45), "45 min")
        self.assertEqual(duration(90), "1 h 30 min")
        self.assertEqual(duration(120), "2 h")

    def test_nav_link_active_only_on_current_page(self):
        request = RequestFactory().get("/services/")
        request.resolver_match = resolve("/services/")
        html = Template(
            '{% load belleza %}{% nav_link "services:list" "Services" %}|{% nav_link "core:home" "Home" %}'
        ).render(Context({"request": request}))
        self.assertEqual(html, '<a class="active" href="/services/">Services</a>|<a href="/">Home</a>')

    def test_nav_anchor_never_active(self):
        request = RequestFactory().get("/")
        request.resolver_match = resolve("/")
        html = Template('{% load belleza %}{% nav_link "core:home" "About" anchor="#origin" %}').render(
            Context({"request": request})
        )
        self.assertEqual(html, '<a href="/#origin">About</a>')

    def test_social_links_contact_variant_uses_local_x_icon(self):
        default = self.client.get(reverse("core:home")).content.decode()
        contact = self.client.get(reverse("core:contact")).content.decode()
        self.assertIn("freepik.com", default)
        self.assertIn("/static/img/x.svg", contact)
