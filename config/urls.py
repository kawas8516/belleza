from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path("", include("apps.bookings.urls")),
    path("services/", include("apps.services.urls")),
    path("account/", include("apps.accounts.urls")),
    path("contact/", include("apps.contact.urls")),
    path("admin/", admin.site.urls),
]
