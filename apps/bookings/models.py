from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.validators import phone_validator
from apps.services.models import Service, Stylist


class BookingQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=Booking.ACTIVE_STATUSES)

    def overlapping(self, stylist, date, start_time, end_time):
        return self.active().filter(
            stylist=stylist, date=date, start_time__lt=end_time, end_time__gt=start_time
        )


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    ACTIVE_STATUSES = (Status.PENDING, Status.CONFIRMED)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    stylist = models.ForeignKey(
        Stylist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Empty means any available stylist.",
    )
    services = models.ManyToManyField(Service, related_name="bookings")

    # Contact details as entered on the booking form (may differ from the account).
    contact_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=13, validators=[phone_validator])

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        ordering = ("-date", "-start_time")

    def __str__(self):
        return f"{self.contact_name} on {self.date:%d %b %Y} at {self.start_time:%H:%M}"

    @property
    def starts_at(self):
        return timezone.make_aware(datetime.combine(self.date, self.start_time))

    @property
    def is_upcoming(self):
        return self.starts_at > timezone.now()

    @property
    def can_cancel(self):
        return self.status in self.ACTIVE_STATUSES and self.is_upcoming
