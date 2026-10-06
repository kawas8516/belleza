from django.utils.functional import SimpleLazyObject

from .models import SiteSettings


def site(request):
    """Expose SiteSettings as `site`; lazy, so pages that don't use it skip the query."""
    return {"site": SimpleLazyObject(SiteSettings.load)}
