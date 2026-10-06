# Belleza

Online salon booking for Pune: customers sign up, browse services and book
an appointment with a stylist. It began as a static HTML/CSS/JS frontend and
is being moved onto Django. The frontend's look is kept exactly as it was
(see [PRODUCT.md](PRODUCT.md)).

## Status

Migration plan, in order:

- [x] **Scaffold**: venv outside the repo, `config/` project, split settings, `.env`, five apps under `apps/`
- [x] **Static + base template**: assets in `static/`, pages in `templates/`, shared nav/footer partials
- [x] **accounts**: custom email-login `User`, signup/login/logout
- [x] **services**: Category / Service / Stylist models, seed data, services page from DB
- [x] **bookings**: booking form with validation, success page, my bookings, cancel
- [x] **contact**: home-page contact form saved to DB, admin
- [x] Tests (51, `manage.py test apps`) + visual check against the original static pages
- [x] **Dynamic content**: hero/intro/about copy, address/phone/email and map in admin (*Site settings*), rendered via a context processor and `{% load belleza %}` tags
- [x] **Booking page redesign**: split into section partials, service/stylist/time chips, server-rendered open time slots, live summary bar
- [ ] Phase 2: django-allauth social login, confirmation emails, deploy

## Stack

- Python 3.13, Django 6.1, python-dotenv
- SQLite in dev
- Plain Django templates (the original HTML/CSS, unchanged in look)

## Project layout

```
config/                 project package
  settings/base.py      shared settings (reads .env)
  settings/dev.py       default for manage.py: DEBUG, sqlite, dev fallback key
  settings/prod.py      DEBUG off, requires SECRET_KEY + ALLOWED_HOSTS, secure cookies/HSTS
apps/
  core/                 home + contact pages, shared phone_validator
  accounts/             custom User (email login), signup/login/logout
  services/             catalogue: Category, Service, Stylist
  bookings/             Booking model, form, validation, my bookings
  contact/              ContactMessage from the home-page form
templates/
  base.html             doctype, fonts, main.css, messages, footer
  partials/             _nav, _footer (variant="contact"), _messages
  core/ accounts/ services/ bookings/
static/
  css/  js/  img/       (formerly css/, *.js, svgfiles/)
```

Where the old static pages went:

| Old file | Now |
|---|---|
| `index.html` | `templates/core/home.html` → `/` |
| `contact.html` | `templates/core/contact.html` → `/contact/` |
| `service.html` | `templates/services/service_list.html` → `/services/` |
| `login.html` / `signup.html` | `templates/accounts/` → `/account/login/`, `/account/signup/` |
| `registration.html` | `templates/bookings/booking_form.html` → `/book/` (login required) |

## Setup

The virtual env lives **outside** the repo, at `C:\Users\kaust\Envs\belleza-venv`.

```bash
# from the repo root
py -3.13 -m venv ../belleza-venv
../belleza-venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY
../belleza-venv/Scripts/python manage.py migrate
../belleza-venv/Scripts/python manage.py createsuperuser
../belleza-venv/Scripts/python manage.py runserver
../belleza-venv/Scripts/python manage.py test apps   # run the test suite
```

`migrate` also seeds the catalogue (5 categories, 25 services, 3 placeholder
stylists) through `apps/services/migrations/0002_seed_catalogue.py`.
Prices and durations are placeholders; edit them in `/admin/`.

To run with production settings, set `DJANGO_SETTINGS_MODULE=config.settings.prod`.

## Editing site content

Log in to `/admin/` → **Core → Site settings** to change the hero text, intro,
about paragraphs, address, phone, email and map. Services, prices and stylists
are under **Services**.

Template helpers (`apps/core/templatetags/belleza.py`, use `{% load belleza %}`):

| Helper | Example | Output |
|---|---|---|
| `{% nav_link %}` | `{% nav_link "services:list" "Services" %}` | link with `class="active"` on the current page |
| `{% copyright_years %}` | `{% copyright_years site.copyright_start_year %}` | `2023–2026` |
| `{% social_links %}` | `{% social_links "contact" %}` | footer social links (contact-page icon variant) |
| `\|rupees` | `{{ 150000\|rupees }}` | `₹1,50,000` |
| `\|duration` | `{{ 90\|duration }}` | `1 h 30 min` |

`site` (the SiteSettings row) is available in every template via the
`apps.core.context_processors.site` context processor.

## Key decisions

- **Login uses email.** `accounts.User` has no username; `full_name` and `phone` are stored on the user.
- **Catalogue:** 5 categories (Hair, Skin, Body, Makeup, Nails). The 3 marked `is_featured` (Hair Styling, Makeup Services, Nail Art) render the same cards as the old static page, on both home and services.
- **Images stay remote URLs** (`URLField`), so Pillow isn't needed.
- **Opening hours** are `BELLEZA_OPEN_TIME` / `BELLEZA_CLOSE_TIME` in settings (10:00–20:00).
- **Social login buttons** are still placeholders (`href="#"`). django-allauth is planned for phase 2.
