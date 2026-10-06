from django.db import models


class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.active().filter(is_featured=True)


class Category(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    card_title = models.CharField(
        max_length=80, blank=True, help_text="Title on the service card; falls back to name."
    )
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_featured = models.BooleanField(
        default=False, help_text="Shown as a card on the home and services pages."
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ("order", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    @property
    def display_title(self):
        return self.card_title or self.name


class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="INR")
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("category__order", "order", "name")
        constraints = [
            models.UniqueConstraint(fields=("category", "slug"), name="unique_service_slug_per_category"),
        ]

    def __str__(self):
        return self.name


class Stylist(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    specialties = models.ManyToManyField(Category, blank=True, related_name="stylists")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
