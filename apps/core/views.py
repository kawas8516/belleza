from django.views.generic import TemplateView

from apps.services.models import Category


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_categories"] = Category.objects.featured()
        return context


class ContactPageView(TemplateView):
    template_name = "core/contact.html"
