from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.utils import timezone

from apps.services.models import Service, Stylist

from .models import Booking


class BookingForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True, category__is_active=True),
        error_messages={"required": "Choose at least one service."},
    )
    stylist = forms.ModelChoiceField(
        queryset=Stylist.objects.filter(is_active=True), required=False
    )

    class Meta:
        model = Booking
        fields = (
            "booked_for_guest",
            "guest_name",
            "guest_phone",
            "guest_email",
            "contact_name",
            "contact_email",
            "contact_phone",
            "services",
            "stylist",
            "date",
            "start_time",
        )
        error_messages = {
            "date": {"required": "Choose a date."},
            "start_time": {"required": "Choose a time."},
            "contact_name": {"required": "Enter your name."},
            "contact_email": {"required": "Enter your email."},
            "contact_phone": {"required": "Enter a phone number we can reach you on."},
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Booker details default to the account when left blank (self-bookings
        # keep the old behaviour of posting them from the form).
        for name in ("contact_name", "contact_email", "contact_phone"):
            self.fields[name].required = False

    def _clean_guest(self, cleaned):
        if not cleaned.get("booked_for_guest"):
            for name in ("guest_name", "guest_phone", "guest_email"):
                cleaned[name] = ""
            return
        labels = {
            "guest_name": "Enter the guest's name.",
            "guest_phone": "Enter a phone number for the guest.",
            "guest_email": "Enter the guest's email.",
        }
        for name, message in labels.items():
            if not cleaned.get(name) and name not in self.errors:
                self.add_error(name, message)

    def _fill_contact(self, cleaned):
        user = self.user
        defaults = {
            "contact_name": getattr(user, "full_name", ""),
            "contact_email": getattr(user, "email", ""),
            "contact_phone": getattr(user, "phone", ""),
        }
        messages = {
            "contact_name": "Enter your name.",
            "contact_email": "Enter your email.",
            "contact_phone": "Enter a phone number we can reach you on.",
        }
        for name, default in defaults.items():
            if not cleaned.get(name):
                cleaned[name] = default
            if not cleaned.get(name) and name not in self.errors:
                self.add_error(name, messages[name])

    def clean(self):
        cleaned = super().clean()
        self._clean_guest(cleaned)
        self._fill_contact(cleaned)
        services = cleaned.get("services")
        date = cleaned.get("date")
        start = cleaned.get("start_time")
        if not services or not date or not start:
            return cleaned

        now = timezone.localtime()
        if date < now.date():
            self.add_error("date", "Choose today or a later date.")
            return cleaned
        horizon = settings.BELLEZA_BOOKING_HORIZON_DAYS
        if date > now.date() + timedelta(days=horizon):
            self.add_error("date", f"We take bookings up to {horizon} days ahead.")
            return cleaned
        if date == now.date() and start <= now.time():
            self.add_error("start_time", "Choose a time later than now.")
            return cleaned

        duration = sum(service.duration_minutes for service in services)
        start_dt = datetime.combine(date, start)
        end_dt = start_dt + timedelta(minutes=duration)
        open_time = settings.BELLEZA_OPEN_TIME
        close_time = settings.BELLEZA_CLOSE_TIME
        if (
            start < open_time
            or end_dt.date() != date
            or end_dt.time() > close_time
        ):
            self.add_error(
                "start_time",
                f"We're open {open_time:%H:%M}–{close_time:%H:%M}. "
                f"Your services take {duration} minutes, so pick a start time that "
                f"finishes by {close_time:%H:%M}.",
            )
            return cleaned

        end = end_dt.time()
        stylist = cleaned.get("stylist")
        if stylist and Booking.objects.overlapping(stylist, date, start, end).exists():
            self.add_error(
                "stylist",
                f"{stylist} is already booked at that time. Choose another time or stylist.",
            )
            return cleaned

        self.instance.end_time = end
        self.instance.total_price = sum(service.price for service in services)
        return cleaned
