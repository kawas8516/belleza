from decimal import Decimal, InvalidOperation

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_link(context, view_name, label, anchor=""):
    """Nav anchor; gets class="active" when it points at the current page (never for #anchors)."""
    href = reverse(view_name) + anchor
    match = getattr(context.get("request"), "resolver_match", None)
    if not anchor and match and match.view_name == view_name:
        return format_html('<a class="active" aria-current="page" href="{}">{}</a>', href, label)
    return format_html('<a href="{}">{}</a>', href, label)


@register.simple_tag
def static_v(path):
    """static() plus ?v=<mtime>, so an edited CSS/JS file is never served stale from cache."""
    url = static(path)
    found = finders.find(path)
    if found and os.path.exists(found):
        return f"{url}?v={int(os.path.getmtime(found))}"
    return url


@register.simple_tag
def copyright_years(start_year):
    """"2023–2026", or just the year once start and current year match."""
    current = timezone.localdate().year
    start = int(start_year or current)
    return str(current) if start >= current else f"{start}–{current}"


# Footer social links. All icons are local white SVGs: the old remote PNG/JPG
# icons carried their own background and showed as a box on the black footer.
SOCIAL_LINKS = [
    {
        "name": "Facebook",
        "url": "https://www.facebook.com/",
        "icon": "img/facebook-svgrepo.svg",
    },
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/",
        "icon": "img/instagram.svg",
    },
    {
        "name": "Twitter",
        "url": "https://www.twitter.com/",
        "icon": "img/x.svg",
    },
]


def _icon_src(path):
    return path if path.startswith(("http://", "https://")) else static(path)


@register.inclusion_tag("partials/_social_links.html")
def social_links(variant=""):
    links = []
    for link in SOCIAL_LINKS:
        links.append({**link, "icon_src": _icon_src(link["icon"])})
    return {"links": links}


@register.filter
def rupees(value):
    """Indian digit grouping with a rupee sign: 150000 -> ₹1,50,000. Drops .00."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    sign = "-" if amount < 0 else ""
    amount = abs(amount).quantize(Decimal("0.01"))
    whole, _, paise = f"{amount:.2f}".partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    suffix = "" if paise == "00" else f".{paise}"
    return f"{sign}₹{whole}{suffix}"


@register.filter
def clock(value):
    """time(15, 0) -> "3:00 PM". One 12-hour format for every booking page."""
    try:
        hour, minute = value.hour, value.minute
    except AttributeError:
        return value
    return f"{hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"


@register.filter
def duration(minutes):
    """45 -> "45 min", 90 -> "1 h 30 min", 120 -> "2 h"."""
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return minutes
    hours, mins = divmod(minutes, 60)
    if not hours:
        return f"{mins} min"
    return f"{hours} h" + (f" {mins} min" if mins else "")
