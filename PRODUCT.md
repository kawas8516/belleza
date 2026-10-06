# Product

## Register

product

## Users

Customers booking salon appointments online in Pune, using Belleza to sign up,
log in, browse services, and book. The auth pages (sign in / sign up) are a
workflow step — the job is to get signed in and move on, not to admire the page.

## Product Purpose

Belleza lets customers book salon services online instead of calling or
walking in. This is also a personal portfolio piece demonstrating frontend
skills (HTML/CSS/JS), so the code and craft are part of what's being shown.

## Brand Personality

Elegant, calm, welcoming — a spa/salon feel: soft, inviting, unhurried.

## Anti-references

Cluttered forms, cold/clinical corporate SaaS login templates, cramped or
misaligned spacing.

## Design Principles

- Auth forms serve the task first — clarity and ease over visual statement.
- Existing colors and elements stay as-is; fixes are structural (spacing,
  alignment, rhythm), not a redesign.
- Confirm before improvising beyond what was asked.
- Consistent spacing rhythm across sign-in and sign-up (they should feel like
  one form, not two different templates).

## Accessibility & Inclusion

Standard good practice: WCAG AA contrast, visible focus states, reduced-motion
support, proper label/input association.

## Implementation Notes

- The site is moving from static HTML to Django (see README.md). Pages now
  live in `templates/`, assets in `static/`.
- The move is structural only: every page must look the same as the
  original static version when logged out. The new UI is limited to the
  logged-in nav ("My bookings" / Logout), flash-message toasts, inline form
  errors, and the booking success / my-bookings pages, which reuse the
  booking page's look.
- Login is by email; the login field placeholder reads "Your Email".
- Site copy and contact details live in the admin (Site settings), not in
  templates. The footer copyright year updates automatically (2023–current).
- The booking page (`/book/`) was redesigned at the user's request, an
  explicit exception to the no-redesign rule: grouped sections, chip
  selectors, open-time slots and a sticky price/duration summary. It keeps
  the original registration look (photo background, translucent panel,
  Arial).
