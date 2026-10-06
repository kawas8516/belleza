from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at", "handled")
    list_filter = ("handled",)
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created_at",)
    actions = ("mark_handled",)

    @admin.action(description="Mark selected messages as handled")
    def mark_handled(self, request, queryset):
        updated = queryset.update(handled=True)
        self.message_user(request, f"{updated} message(s) marked handled.")
