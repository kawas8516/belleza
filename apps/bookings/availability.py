"""Time-slot availability for the booking page.

Slots are a preview for the customer; BookingForm.clean stays the source of
truth when the booking is actually submitted.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from .models import Booking


@dataclass(frozen=True)
class Slot:
    time: time
    available: bool
    reason: str  # "" when available, else "past" or "booked"
    free_minutes: int  # minutes until the stylist's next booking or closing

    @property
    def value(self):
        return self.time.strftime("%H:%M")


def _minutes(t):
    return t.hour * 60 + t.minute


def day_slots(date, stylist=None, step=None):
    step = step or settings.BELLEZA_SLOT_MINUTES
    open_m = _minutes(settings.BELLEZA_OPEN_TIME)
    close_m = _minutes(settings.BELLEZA_CLOSE_TIME)

    busy = []  # (start, end) minute pairs for the chosen stylist's active bookings
    if stylist is not None:
        busy = sorted(
            (_minutes(start), _minutes(end))
            for start, end in Booking.objects.active()
            .filter(stylist=stylist, date=date)
            .values_list("start_time", "end_time")
        )

    now = timezone.localtime()
    now_m = _minutes(now.time()) if date == now.date() else None
    if date < now.date():
        now_m = close_m

    slots = []
    for start in range(open_m, close_m - step + 1, step):
        slot_end = start + step
        overlaps = any(b_start < slot_end and b_end > start for b_start, b_end in busy)
        next_start = min((b_start for b_start, _ in busy if b_start >= start), default=close_m)
        if now_m is not None and start <= now_m:
            reason = "past"
        elif overlaps:
            reason = "booked"
        else:
            reason = ""
        slots.append(
            Slot(
                time=time(start // 60, start % 60),
                available=not reason,
                reason=reason,
                free_minutes=0 if reason else min(next_start, close_m) - start,
            )
        )
    return slots


def end_time_for(start, minutes):
    """Clock time `minutes` after `start` (same day)."""
    return (datetime.combine(datetime.min, start) + timedelta(minutes=minutes)).time()
