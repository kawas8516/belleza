from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand", {"fields": ("brand_name", "footer_brand", "copyright_start_year")}),
        ("Contact", {"fields": ("address", "phone", "email")}),
        ("Home page copy", {"fields": ("hero_title", "hero_subtitle", "intro_text", "about_text")}),
        ("Map", {"fields": ("map_embed_url",)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
