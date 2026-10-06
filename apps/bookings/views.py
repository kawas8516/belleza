from dataclasses import replace
from datetime import date, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from apps.services.models import Category, Service

from .availability import day_slots, end_time_for
from .forms import BookingForm
from .models import Booking


class BookingCreateView(LoginRequiredMixin, CreateView):
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    # Fields carried over when "Show times" re-renders the page via GET.
    REFRESH_FIELDS = ("contact_name", "contact_email", "contact_phone", "stylist", "date", "start_time")
    # Where each field's error in the summary links to.
    ERROR_ANCHORS = {
        "services": "section-services",
        "stylist": "section-stylist",
        "start_time": "section-time",
        "date": "id_date",
        NON_FIELD_ERRORS: "booking-form",
    }

    def get(self, request, *args, **kwargs):
        # "Show times" submits the whole form via GET; keep the CSRF token out of the URL.
        if "csrfmiddlewaretoken" in request.GET:
            query = request.GET.copy()
            del query["csrfmiddlewaretoken"]
            return redirect(f"{request.path}?{query.urlencode()}#section-time")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        user = self.request.user
        initial = {
            "contact_name": user.full_name,
            "contact_email": user.email,
            "contact_phone": user.phone,
        }
        query = self.request.GET
        for field in self.REFRESH_FIELDS:
            if field in query:
                initial[field] = query[field]
        if "services" in query:
            initial["services"] = query.getlist("services")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        today = timezone.localdate()
        horizon = today + timedelta(days=settings.BELLEZA_BOOKING_HORIZON_DAYS)

        categories = list(
            Category.objects.active().prefetch_related(
                Prefetch("services", queryset=Service.objects.filter(is_active=True))
            )
        )
        stylists = list(form.fields["stylist"].queryset.prefetch_related("specialties"))
        selected_service_ids = {str(pk) for pk in (form["services"].value() or [])}
        selected_stylist = str(form["stylist"].value() or "")
        selected_date = _as_date(form["date"].value())
        date_notice = ""
        if selected_date and selected_date < today:
            date_notice, selected_date = "That date has passed. Pick today or a later date.", None
        elif selected_date and selected_date > horizon:
            date_notice = f"We take bookings up to {settings.BELLEZA_BOOKING_HORIZON_DAYS} days ahead."
            selected_date = None
        selected_time = str(form["start_time"].value() or "")[:5]

        chosen = [
            service
            for category in categories
            for service in category.services.all()
            if str(service.pk) in selected_service_ids
        ]
        minutes = sum(service.duration_minutes for service in chosen)

        slots = []
        if selected_date:
            stylist = next((s for s in stylists if str(s.pk) == selected_stylist), None)
            slots = [
                replace(slot, available=False, reason="short")
                if slot.available and minutes > slot.free_minutes
                else slot
                for slot in day_slots(selected_date, stylist)
            ]
        if selected_time not in {slot.value for slot in slots if slot.available}:
            selected_time = ""

        end_time = None
        if selected_time and minutes:
            end_time = end_time_for(time.fromisoformat(selected_time), minutes)

        context.update(
            categories=categories,
            stylists=stylists,
            selected_service_ids=selected_service_ids,
            selected_stylist=selected_stylist,
            selected_date=selected_date,
            date_notice=date_notice,
            selected_time=selected_time,
            slots=slots,
            has_open_slot=any(slot.available for slot in slots),
            error_links=[
                {"anchor": self.ERROR_ANCHORS.get(field, f"id_{field}"), "message": message}
                for field, messages_ in form.errors.items()
                for message in messages_
            ],
            date_min=today,
            date_max=horizon,
            summary={
                "count": len(chosen),
                "minutes": minutes,
                "total": sum(service.price for service in chosen),
                "end_time": end_time,
            },
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        form.instance.customer = self.request.user
        booking = form.save()
        return redirect("bookings:success", pk=booking.pk)


def _as_date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


@login_required
def booking_success(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    return render(request, "bookings/booking_success.html", {"booking": booking})


class MyBookingsView(LoginRequiredMixin, ListView):
    template_name = "bookings/my_bookings.html"
    context_object_name = "bookings"

    def get_queryset(self):
        return (
            Booking.objects.filter(customer=self.request.user)
            .select_related("stylist")
            .prefetch_related("services")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = list(context["bookings"])
        context["upcoming"] = sorted(
            (b for b in bookings if b.is_upcoming), key=lambda b: (b.date, b.start_time)
        )
        context["past"] = [b for b in bookings if not b.is_upcoming]
        return context


@login_required
@require_POST
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    if booking.can_cancel:
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "Your booking has been cancelled.")
    else:
        messages.error(request, "This booking can no longer be cancelled.")
    return redirect("bookings:mine")
