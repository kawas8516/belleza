from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("book/", views.BookingCreateView.as_view(), name="create"),
    path("book/success/<int:pk>/", views.booking_success, name="success"),
    path("book/<int:pk>/cancel/", views.booking_cancel, name="cancel"),
    path("account/bookings/", views.MyBookingsView.as_view(), name="mine"),
]
