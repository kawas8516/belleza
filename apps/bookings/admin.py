from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("contact_name", "customer", "date", "start_time", "end_time", "stylist", "status", "total_price")
    list_filter = ("status", "date", "stylist")
    search_fields = ("contact_name", "contact_email", "contact_phone", "customer__email")
    date_hierarchy = "date"
    filter_horizontal = ("services",)
    list_select_related = ("customer", "stylist")
    readonly_fields = ("created_at",)
    actions = ("mark_confirmed", "mark_completed")

    @admin.action(description="Mark selected bookings as confirmed")
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status=Booking.Status.CONFIRMED)
        self.message_user(request, f"{updated} booking(s) confirmed.")

    @admin.action(description="Mark selected bookings as completed")
    def mark_completed(self, request, queryset):
        updated = queryset.update(status=Booking.Status.COMPLETED)
        self.message_user(request, f"{updated} booking(s) completed.")
