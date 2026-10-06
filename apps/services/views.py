from django.views.generic import ListView

from .models import Category


class ServiceListView(ListView):
    template_name = "services/service_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.featured()
