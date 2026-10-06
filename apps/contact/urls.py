from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("send/", views.contact_submit, name="submit"),
]
