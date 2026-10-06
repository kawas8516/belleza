"""Seed SiteSettings with the copy and contact details from the original static index.html."""

from django.db import migrations

SITE_SETTINGS = {'hero_title': 'Book your Styling Session on Tips',
 'hero_subtitle': 'Experience the convenience of booking salon appointments online with Belleza',
 'intro_text': 'Introducing Belleza your ultimate online selling booking platform in Pune. We '
               "understand the importance of convenience and time saving in today's fastest world. "
               'With belleza, You can effortlessly book appointments at your favorite salons, '
               'right from the comfort of your own home. Say goodbye to the long waiting times and '
               'last night cancellations. Our user friendly interface and extensive cell network '
               'ensures that you can easily find and book perfect beauty services that suit your '
               'needs. Experience hassle-free salon bookings with Belleza and let us take care of '
               'your beauty needs, so you can focus on looking and feeling your best.',
 'about_text': 'Welcome to Belleza, the premier online salon booking platform. Started in Pune, we '
               'are dedicated to providing a convenient and hassle-free way for you to book salon '
               'services from the comfort of your own home. With our user-friendly website and '
               'extensive network of trusted salons, you can easily find and book appointments for '
               'a wide range of beauty treatments. Whether you need a haircut, a manicure, or a '
               "relaxing massage, we've got you covered. Experience the convenience of Belleza and "
               'let us help you look and feel your best.\n'
               '\n'
               "At Belleza, we understand the importance of quality and professionalism. That's "
               'why we have carefully curated a selection of top-notch salons that offer '
               'exceptional services. Our goal is to connect you with the best salons in your '
               'area, ensuring that you receive the highest level of care and expertise. With '
               'Belleza, you can say goodbye to long waiting times and last-minute cancellations. '
               'Book your next salon appointment with us and enjoy a seamless and enjoyable beauty '
               'experience.',
 'map_embed_url': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3783.4592721510553!2d73.78622731074397!3d18.508136569481422!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bc2be4e9e176c53%3A0x14ab98597320bbdb!2sLohia%20Jain%20IT%20Park!5e0!3m2!1sen!2sin!4v1700420872864!5m2!1sen!2sin',
 'address': 'Jain IT Park, Paud Road, Kothrud, Pune',
 'phone': '123-456-7890',
 'email': 'info@mysite.com',
 'brand_name': 'Belleza',
 'footer_brand': 'Bellezza',
 'copyright_start_year': 2023}


def seed(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    SiteSettings.objects.update_or_create(pk=1, defaults=SITE_SETTINGS)


def unseed(apps, schema_editor):
    apps.get_model("core", "SiteSettings").objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_site_settings"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
