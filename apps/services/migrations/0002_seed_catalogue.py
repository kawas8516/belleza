"""
Seed the catalogue from the original static site.

Service names come from the old registration.html; featured card titles,
descriptions and images from the old service.html. Durations and prices
(INR) are placeholders -- edit them in the admin.
"""

from decimal import Decimal

from django.db import migrations
from django.utils.text import slugify

CATEGORIES = [
    {
        "name": "Hair",
        "card_title": "Hair Styling",
        "description": "Our professional stylists will create a stunning hairstyle that suits your personality and preferences.",
        "image_url": "https://images.pexels.com/photos/3992874/pexels-photo-3992874.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
        "is_featured": True,
        "services": [
            ("Haircut", 45, "500"),
            ("Color and Haircut", 120, "2500"),
            ("Hair Treatment", 60, "1500"),
            ("Voluming hair treatment", 60, "1800"),
            ("Healthy scalp treatment", 45, "1200"),
            ("Luxury blow dry", 45, "800"),
            ("Shine and gloss treatment", 60, "1600"),
        ],
    },
    {
        "name": "Skin",
        "services": [
            ("Sugar Waxing", 45, "700"),
            ("Laser hair removal", 60, "3500"),
            ("Brightening facial", 60, "1800"),
            ("Dermaplaning", 45, "2000"),
            ("Microneedling", 60, "4500"),
            ("Retinol skincare", 45, "2200"),
            ("Chemical peels", 45, "3000"),
        ],
    },
    {
        "name": "Body",
        "services": [
            ("Contouring body wrap", 90, "3500"),
            ("Slimming body treatment", 90, "4000"),
            ("Scrub and Mud treatment", 60, "2500"),
            ("Detox dry brushing", 45, "1500"),
        ],
    },
    {
        "name": "Makeup",
        "card_title": "Makeup Services",
        "description": "Get the perfect makeup look for any occasion with our expert makeup artists.",
        "image_url": "https://images.pexels.com/photos/1327353/pexels-photo-1327353.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
        "is_featured": True,
        "services": [
            ("Party makeup", 60, "2000"),
            ("Bridal makeup", 150, "12000"),
            ("HD makeup", 90, "4000"),
        ],
    },
    {
        "name": "Nails",
        "card_title": "Nail Art",
        "description": "Indulge in our nail art services and flaunt beautiful, well-designed nails.",
        "image_url": "https://images.pexels.com/photos/4677854/pexels-photo-4677854.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2",
        "is_featured": True,
        "services": [
            ("Manicure", 45, "600"),
            ("Pedicure", 60, "800"),
            ("Nail art", 60, "1000"),
            ("Gel extensions", 90, "1800"),
        ],
    },
]

# Placeholder stylists; specialties are category names.
STYLISTS = [
    ("Ananya Kulkarni", "Senior hair stylist and colourist.", ["Hair"]),
    ("Riya Deshpande", "Makeup artist and nail technician.", ["Makeup", "Nails"]),
    ("Meera Joshi", "Skin and body therapist.", ["Skin", "Body"]),
]


def seed(apps, schema_editor):
    Category = apps.get_model("services", "Category")
    Service = apps.get_model("services", "Service")
    Stylist = apps.get_model("services", "Stylist")

    categories = {}
    for order, data in enumerate(CATEGORIES):
        category = Category.objects.create(
            name=data["name"],
            slug=slugify(data["name"]),
            card_title=data.get("card_title", ""),
            description=data.get("description", ""),
            image_url=data.get("image_url", ""),
            is_featured=data.get("is_featured", False),
            order=order,
        )
        categories[category.name] = category
        for service_order, (name, minutes, price) in enumerate(data["services"]):
            Service.objects.create(
                category=category,
                name=name,
                slug=slugify(name),
                duration_minutes=minutes,
                price=Decimal(price),
                order=service_order,
            )

    for name, bio, specialties in STYLISTS:
        stylist = Stylist.objects.create(name=name, bio=bio)
        stylist.specialties.set([categories[c] for c in specialties])


def unseed(apps, schema_editor):
    apps.get_model("services", "Stylist").objects.filter(name__in=[s[0] for s in STYLISTS]).delete()
    Category = apps.get_model("services", "Category")
    Service = apps.get_model("services", "Service")
    slugs = [slugify(c["name"]) for c in CATEGORIES]
    Service.objects.filter(category__slug__in=slugs).delete()
    Category.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
