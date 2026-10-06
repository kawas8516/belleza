from django.contrib import admin

from .models import Category, Service, Stylist


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0
    fields = ("name", "slug", "duration_minutes", "price", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "card_title", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "duration_minutes", "price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Stylist)
class StylistAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active", "specialties")
    filter_horizontal = ("specialties",)
