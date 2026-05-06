# Ravinarayan PG & Tiffin Service — Website

Mobile-first Django site for browsing tiffin plans, picking add-ons, and placing
orders — confirmed via WhatsApp. Owner manages everything from `/django-admin/`.

## Stack

- **Django 5** + Django templates (server-rendered)
- **SQLite** (zero-setup, fine for this scale)
- Custom CSS + a tiny vanilla JS file (no framework)
- Real Django auth — login required for the admin order dashboard

## What the owner can edit (no code changes)

Everything below is editable from `/django-admin/`:

- **Site Settings** (singleton): brand name, tagline, **phone**, **WhatsApp number**, email, address, hours, social links
- **Delivery Areas**: add/disable/reorder
- **Plans**: name, price, items, badge, sort order, active toggle
- **Add-ons**: chapati, raita, sweets, curd, lassi, papad, etc. — name, price, unit, icon, active
- **Daily Menu**: 7 days × 2 meals (lunch / dinner) — what's served when
- **Orders**: full history, status changes, search/filter

The **today's menu** on the home page automatically picks the right row from
DailyMenu using `date.today().weekday()` so it changes by itself every day.

## Customer flow

1. Home → see today's menu, plans, why-us
2. Order page → pick plan card, +/− add-ons, fill name/phone/address, pick date/time
3. Live summary panel updates total in real time
4. Submit → server saves the Order, redirects to success page
5. Success page has a big "Send Order on WhatsApp" button that opens WhatsApp
   with a pre-filled message containing every detail (order ID, plan, add-ons,
   address, date, **total ₹**)
6. Owner sees the order in the admin dashboard and confirms via WhatsApp/phone

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate          # also seeds plans / addons / menu / settings
python manage.py createsuperuser  # or use the one already created
python manage.py runserver
```

## Authentication

Two admin surfaces, both behind real Django auth:

| Surface | URL | Purpose |
|---|---|---|
| Order dashboard | `/admin-orders/` | Quick view, status updates |
| Full Django admin | `/django-admin/` | Edit menus, plans, add-ons, contact info |

`@login_required` + `@user_passes_test(is_staff)` is applied to all admin
views. Unauthenticated requests redirect to `/admin-login/?next=…`.

## Logo

Save the brand logo to `static/img/logo.png` (used in the navbar + hero).
If the file is missing, the navbar falls back to a text wordmark — the site
keeps working. Recommended size: at least 480px tall, transparent background.

## Layout

```
tiffin.ravinarayn/
├── manage.py
├── requirements.txt
├── tiffin_project/        # Django settings & root URLs
├── tiffin/
│   ├── models.py          # SiteSettings, Plan, Addon, DailyMenu, DeliveryArea, Order
│   ├── forms.py           # OrderForm with plan + add-on quantities
│   ├── views.py           # Public pages, custom login, admin order dashboard
│   ├── admin.py           # /django-admin/ for everything editable
│   ├── seed.py            # Seed defaults (used by 0002_seed_data migration)
│   ├── context_processors.py
│   ├── urls.py
│   ├── migrations/
│   └── templates/tiffin/
│       ├── base.html, home.html, menu.html
│       ├── order_form.html, order_success.html
│       ├── login.html, admin_orders.html
│       └── components/{navbar,footer,plan_card,whatsapp_button}.html
└── static/
    ├── css/styles.css
    ├── js/app.js
    └── img/logo.png       # ← save the brand logo here
```

## Security

- **Auth**: Django's session-based auth + `is_staff` check on admin pages
- **CSRF**: Every form includes `{% csrf_token %}`; middleware enforced
- **XSS**: Django auto-escapes — verified on order summary, WhatsApp `href`
  is properly URL-encoded
- **Open-redirect protection**: `?next=` parameter is restricted to same-origin
  paths (must start with `/`)
- **Order codes**: `secrets.choice` (cryptographically random, 6 chars,
  no `O/0/I/1`)
- **Input validation**: server-side in [tiffin/forms.py](tiffin/forms.py)
  (phone regex, length, plan/area FK whitelist, date window 0-60 days,
  qty 1-100)
- **Headers**: `X-Frame-Options: DENY`, nosniff, XSS filter; HSTS + secure
  cookies + SSL redirect when `DJANGO_DEBUG=0`

### Production checklist
- [ ] `DJANGO_SECRET_KEY` from env / secrets manager
- [ ] `DJANGO_DEBUG=0`
- [ ] `DJANGO_ALLOWED_HOSTS=yourdomain.com`
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com`
- [ ] Reverse proxy + TLS (see [deploy/DEPLOY.md](deploy/DEPLOY.md))
- [ ] Rate-limit `/order/` POST (nginx / Cloudflare)
- [ ] `python manage.py collectstatic` (WhiteNoise serves from `STATIC_ROOT`)
- [ ] Daily DB backup (SQLite file, or move to Postgres)
- [ ] Rotate the seeded admin password

For a step-by-step VPS deploy (Ubuntu 24.04 + nginx + gunicorn + Let's Encrypt),
see **[deploy/DEPLOY.md](deploy/DEPLOY.md)**.

## Future-proofing

- **Payments**: add a `Payment` model FK'd to `Order`, plug Razorpay/UPI on
  the success page
- **Customer login**: enable Django's `django.contrib.auth` views and FK
  `Order.customer = ForeignKey(User)`
- **Subscriptions**: add a `Subscription` model + management command to
  auto-create daily orders
