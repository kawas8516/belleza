from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.services.models import Service, Stylist

from .availability import day_slots
from .models import Booking

User = get_user_model()


class BookingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="asha@example.com", password="Belleza-2026!", full_name="Asha", phone="+919876543210"
        )
        self.client.force_login(self.user)
        self.haircut = Service.objects.get(slug="haircut")  # 45 min, 500
        self.blow_dry = Service.objects.get(slug="luxury-blow-dry")  # 45 min, 800
        self.stylist = Stylist.objects.first()
        self.tomorrow = timezone.localdate() + timedelta(days=1)

    def post_booking(self, **overrides):
        data = {
            "contact_name": "Asha",
            "contact_email": "asha@example.com",
            "contact_phone": "+919876543210",
            "services": [self.haircut.pk, self.blow_dry.pk],
            "stylist": self.stylist.pk,
            "date": self.tomorrow.isoformat(),
            "start_time": "11:00",
        }
        data.update(overrides)
        return self.client.post(reverse("bookings:create"), data)


class BookingCreateTests(BookingTestCase):
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("bookings:create"))
        self.assertRedirects(response, reverse("accounts:login") + "?next=/book/")

    def test_form_prefilled_and_lists_catalogue(self):
        response = self.client.get(reverse("bookings:create"))
        self.assertContains(response, 'value="Asha"')
        self.assertContains(response, 'name="services"', count=25)
        self.assertContains(response, self.stylist.name)

    def test_valid_booking_computes_end_time_and_price(self):
        response = self.post_booking()
        booking = Booking.objects.get()
        self.assertRedirects(response, reverse("bookings:success", args=[booking.pk]))
        self.assertEqual(booking.customer, self.user)
        self.assertEqual(booking.end_time, time(12, 30))
        self.assertEqual(booking.total_price, Decimal("1300"))
        self.assertEqual(booking.services.count(), 2)
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_any_stylist_allowed(self):
        self.post_booking(stylist="")
        self.assertIsNone(Booking.objects.get().stylist)

    def test_past_date_rejected(self):
        response = self.post_booking(date=(timezone.localdate() - timedelta(days=1)).isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())
        self.assertContains(response, "today or a later date")

    def test_no_services_rejected(self):
        response = self.post_booking(services=[])
        self.assertContains(response, "Choose at least one service")
        self.assertFalse(Booking.objects.exists())

    def test_before_opening_rejected(self):
        response = self.post_booking(start_time="09:00")
        self.assertContains(response, "open 10:00")
        self.assertFalse(Booking.objects.exists())

    def test_running_past_closing_rejected(self):
        # 90 minutes of services starting 19:00 ends 20:30, after closing.
        response = self.post_booking(start_time="19:00")
        self.assertContains(response, "open 10:00")
        self.assertFalse(Booking.objects.exists())

    def test_stylist_overlap_rejected(self):
        self.post_booking(start_time="11:00")  # 11:00-12:30
        response = self.post_booking(start_time="12:00", services=[self.haircut.pk])
        self.assertContains(response, "already booked")
        self.assertEqual(Booking.objects.count(), 1)

    def test_back_to_back_allowed(self):
        self.post_booking(start_time="11:00")  # ends 12:30
        self.post_booking(start_time="12:30", services=[self.haircut.pk])
        self.assertEqual(Booking.objects.count(), 2)

    def test_cancelled_booking_frees_slot(self):
        self.post_booking(start_time="11:00")
        Booking.objects.update(status=Booking.Status.CANCELLED)
        self.post_booking(start_time="11:00")
        self.assertEqual(Booking.objects.count(), 2)


class BookingOwnershipTests(BookingTestCase):
    def setUp(self):
        super().setUp()
        self.post_booking()
        self.booking = Booking.objects.get()
        self.other = User.objects.create_user(email="other@example.com", password="x-Belleza-2026", full_name="Other")

    def test_success_page_for_owner(self):
        response = self.client.get(reverse("bookings:success", args=[self.booking.pk]))
        self.assertContains(response, "Booking received")
        self.assertContains(response, "Haircut")

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("bookings:success", args=[self.booking.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("bookings:cancel", args=[self.booking.pk])).status_code, 404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)

    def test_my_bookings_lists_upcoming(self):
        response = self.client.get(reverse("bookings:mine"))
        self.assertContains(response, "Haircut")
        self.assertContains(response, ">Cancel<")

    def test_cancel(self):
        response = self.client.post(reverse("bookings:cancel", args=[self.booking.pk]))
        self.assertRedirects(response, reverse("bookings:mine"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

    def test_cannot_cancel_past_booking(self):
        Booking.objects.filter(pk=self.booking.pk).update(date=date(2020, 1, 1))
        self.client.post(reverse("bookings:cancel", args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.PENDING)


class AvailabilityTests(BookingTestCase):
    def slot(self, slots, value):
        return next(s for s in slots if s.value == value)

    def test_full_day_of_slots(self):
        slots = day_slots(self.tomorrow, self.stylist)
        self.assertEqual(slots[0].value, "10:00")
        self.assertEqual(slots[-1].value, "19:30")
        self.assertTrue(all(s.available for s in slots))
        self.assertEqual(self.slot(slots, "19:00").free_minutes, 60)

    def test_booked_slots_disabled_and_free_minutes_shortened(self):
        self.post_booking(start_time="11:00")  # 11:00-12:30
        slots = day_slots(self.tomorrow, self.stylist)
        self.assertEqual(self.slot(slots, "10:00").free_minutes, 60)
        for value in ("11:00", "11:30", "12:00"):
            self.assertEqual(self.slot(slots, value).reason, "booked")
        self.assertTrue(self.slot(slots, "12:30").available)

    def test_any_stylist_ignores_stylist_bookings(self):
        self.post_booking(start_time="11:00")
        self.assertTrue(self.slot(day_slots(self.tomorrow, None), "11:00").available)

    def test_cancelled_booking_frees_slots(self):
        self.post_booking(start_time="11:00")
        Booking.objects.update(status=Booking.Status.CANCELLED)
        self.assertTrue(self.slot(day_slots(self.tomorrow, self.stylist), "11:00").available)

    def test_past_slots_today(self):
        now = timezone.localtime()
        slots = day_slots(now.date(), self.stylist)
        past = [s for s in slots if s.time <= now.time()]
        self.assertTrue(all(s.reason == "past" for s in past))


class BookingPageTests(BookingTestCase):
    def test_empty_state_before_date(self):
        response = self.client.get(reverse("bookings:create"))
        self.assertContains(response, "Pick a date to see open times.")
        self.assertContains(response, "Choose at least one service")

    def test_show_times_keeps_selections_and_renders_slots(self):
        self.post_booking(start_time="11:00")
        response = self.client.get(
            reverse("bookings:create"),
            {
                "services": [self.haircut.pk],
                "stylist": self.stylist.pk,
                "date": self.tomorrow.isoformat(),
                "contact_name": "Asha K",
            },
        )
        content = response.content.decode()
        self.assertIn(f'id="service-{self.haircut.pk}" name="services" value="{self.haircut.pk}"', content)
        self.assertRegex(content, rf'id="service-{self.haircut.pk}"[^>]* checked')
        self.assertRegex(content, rf'id="stylist-{self.stylist.pk}"[^>]* checked')
        self.assertContains(response, 'value="Asha K"')
        self.assertRegex(content, r'id="slot-1100"[^>]* disabled')
        self.assertNotRegex(content, r'id="slot-1300"[^>]* disabled')
        self.assertNotContains(response, "error-summary")
        self.assertContains(response, "1 service · 45 min")

    def test_csrf_token_stripped_from_show_times_url(self):
        response = self.client.get(
            reverse("bookings:create"), {"csrfmiddlewaretoken": "abc", "date": self.tomorrow.isoformat()}
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("csrfmiddlewaretoken", response["Location"])
        self.assertIn(f"date={self.tomorrow.isoformat()}", response["Location"])

    def test_beyond_horizon_rejected(self):
        far = timezone.localdate() + timedelta(days=61)
        response = self.post_booking(date=far.isoformat())
        self.assertContains(response, "up to 60 days ahead")
        self.assertFalse(Booking.objects.exists())

    def test_error_summary_links_to_sections(self):
        response = self.post_booking(services=[], start_time="")
        self.assertContains(response, 'href="#section-services"')
        self.assertContains(response, 'href="#section-time"')
        self.assertContains(response, "Choose a time.")

    def test_summary_with_selected_slot(self):
        response = self.client.get(
            reverse("bookings:create"),
            {
                "services": [self.haircut.pk, self.blow_dry.pk],
                "date": self.tomorrow.isoformat(),
                "start_time": "11:00",
            },
        )
        self.assertContains(response, "2 services · 1 h 30 min · ends 12:30")
        self.assertContains(response, "₹1,300")


class BookingPolishTests(BookingTestCase):
    def test_date_beyond_window_explains_on_show_times(self):
        far = timezone.localdate() + timedelta(days=90)
        response = self.client.get(reverse("bookings:create"), {"date": far.isoformat()})
        self.assertContains(response, "We take bookings up to 60 days ahead.")
        self.assertNotContains(response, "Pick a date to see open times.")

    def test_past_date_explains_on_show_times(self):
        past = timezone.localdate() - timedelta(days=3)
        response = self.client.get(reverse("bookings:create"), {"date": past.isoformat()})
        self.assertContains(response, "That date has passed.")

    def test_sections_have_headings_and_back_link(self):
        response = self.client.get(reverse("bookings:create"))
        for title in ("Your details", "Services", "Stylist", "Date &amp; time"):
            self.assertContains(response, f"<legend><h2>{title}</h2></legend>")
        self.assertContains(response, 'class="booking-back" href="/"')
