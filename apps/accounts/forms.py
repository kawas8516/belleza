from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    agree_terms = forms.BooleanField(
        required=True,
        error_messages={"required": "Please accept the Terms of service to continue."},
    )

    class Meta:
        model = User
        fields = ("full_name", "email")


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)
