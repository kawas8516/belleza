from django.db import models


class SiteSettings(models.Model):
    """Site-wide content edited in the admin. There is only ever one row."""

    brand_name = models.CharField(max_length=60, default="Belleza")
    footer_brand = models.CharField(max_length=60, default="Belleza")

    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    copyright_start_year = models.PositiveSmallIntegerField(default=2023)
    map_embed_url = models.URLField(max_length=1000, blank=True)

    hero_title = models.CharField(max_length=120, blank=True)
    hero_subtitle = models.CharField(max_length=200, blank=True)
    intro_text = models.TextField(blank=True)
    about_text = models.TextField(blank=True, help_text="Separate paragraphs with a blank line.")

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # The singleton row is never deleted; edit it instead.
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
