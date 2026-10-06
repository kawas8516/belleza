from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    r"^\+?\d{10,13}$",
    "Enter a valid phone number: 10-13 digits, optionally starting with +.",
)
