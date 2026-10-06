from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ContactForm


@require_POST
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks! We'll get back to you soon.")
    else:
        errors = "; ".join(
            f"{form.fields[field].label}: {' '.join(errs)}" for field, errs in form.errors.items()
        )
        messages.error(request, f"Your message wasn't sent. {errors}")
    return redirect(reverse("core:home") + "#form-loc")
