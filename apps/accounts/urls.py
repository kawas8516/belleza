from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", views.BellezaLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
