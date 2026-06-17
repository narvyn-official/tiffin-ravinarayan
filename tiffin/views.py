from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import seo
from .catalog import visible_plans
from .forms import OrderForm, TIFFIN_DINNER_CUTOFF, TIFFIN_LUNCH_CUTOFF
from .geo import MAX_DELIVERY_KM
from .local_seo import SERVICE_AREAS
from .models import Addon, DailyMenu, DeliveryArea, Order, Plan, SiteSettings


FAQS = [
    (
        "How does the tiffin service work?",
        "Pick a plan, choose lunch / dinner / both, fill your details on the order form, "
        "and confirm on WhatsApp. We deliver fresh-cooked meals to your door at lunch (by 1 PM) "
        "or dinner (by 8:30 PM). No app to install, no payment online."
    ),
    (
        "What's the price of one tiffin?",
        "₹80 per meal for the Daily Tiffin (4 roti, sabzi, dal, rice, salad). For long-term "
        "subscribers, our PG Monthly Plan is ₹3500 per month for lunch + dinner, or ₹2000 per "
        "month for either lunch or dinner."
    ),
    (
        "Do you deliver near me?",
        "We currently deliver in Metcity, Yakubpur and Jhajjar, Haryana. On the order page, "
        "tap 'Set delivery location', search for your address or use "
        "GPS — the map will show whether you're inside our 4 km delivery circle. If you're outside, you "
        "can still pick up from the counter."
    ),
    (
        "Is the food vegetarian?",
        "Yes. All our tiffin plans are 100% vegetarian. Cooked in a clean, FSSAI-compliant kitchen "
        "with masks, hairnets and gloves. Less oil, balanced spice — homestyle taste."
    ),
    (
        "Can I get both lunch and dinner?",
        "Yes — pick 'Lunch + Dinner' on the order form. The quantity automatically doubles "
        "(e.g. ordering 5 means 5 lunch + 5 dinner = 10 meals)."
    ),
    (
        "Do I need to pay online?",
        "No. There's no online payment. Orders are confirmed on WhatsApp and you pay on delivery "
        "or via UPI to the owner. We're a small local kitchen — keeping it simple and human."
    ),
    (
        "What if I want to skip a day or cancel my monthly plan?",
        "Just message us on WhatsApp before 9 AM that day for lunch, or before 5 PM for dinner. "
        "Monthly plans can be paused; remaining days roll over to the next month."
    ),
    (
        "Do you cater for offices, PGs and corporate orders?",
        "Yes. Bulk and corporate orders are welcome. Send us a WhatsApp message with the headcount "
        "and address and we'll customize a plan."
    ),
]


WHY_CHOOSE_US = [
    {"icon": "🌿", "title": "Fresh Daily", "text": "Cooked the same morning — never reheated from yesterday."},
    {"icon": "🛡", "title": "Hygienic Kitchen", "text": "FSSAI norms, sealed containers, gloves and head-caps."},
    {"icon": "₹",  "title": "Affordable", "text": "Free delivery up to 2 km, then ₹10 per 2 km. Max delivery 4 km."},
    {"icon": "⏱", "title": "On Time", "text": "Lunch by 1 PM, dinner by 8:30 PM — every day."},
    {"icon": "❤️", "title": "Homestyle Taste", "text": "Less oil, balanced spice — like ghar ka khaana."},
    {"icon": "📞", "title": "Easy to Order", "text": "Order on WhatsApp or in 30 seconds on this site."},
]


def _todays_menu():
    """One query for both meals, cheaper than two filtered .first() calls."""
    dow = timezone.localdate().weekday()
    rows = list(DailyMenu.objects.filter(day_of_week=dow, is_active=True))
    lunch = next((r for r in rows if r.meal_time == DailyMenu.MEAL_LUNCH), None)
    dinner = next((r for r in rows if r.meal_time == DailyMenu.MEAL_DINNER), None)
    return lunch, dinner


def _set_anonymous_cache(response, max_age=120):
    """Allow shared/proxy caches to hold the response for a couple of minutes
    on anonymous visits. Avoids serving cached navbar to logged-in staff."""
    response["Cache-Control"] = f"public, max-age={max_age}, stale-while-revalidate=600"
    response["Vary"] = "Cookie, Accept-Encoding"
    return response


def _minutes_after_midnight(value):
    return value.hour * 60 + value.minute


# ---------- public pages ----------------------------------------------------

def home(request):
    lunch, dinner = _todays_menu()
    site = SiteSettings.get()
    plans = list(visible_plans())
    areas = list(DeliveryArea.objects.filter(is_active=True))

    # JSON-LD for SEO: a restaurant snippet, today's menu, and an FAQ page
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.website_jsonld(request, site),
        seo.faq_jsonld(FAQS),
    ]
    menu_payload = seo.menu_jsonld(request, site, lunch, dinner)
    if menu_payload:
        jsonld.append(menu_payload)

    ctx = {
        "plans": plans,
        "todays_lunch": lunch,
        "todays_dinner": dinner,
        "today_label": timezone.localdate().strftime("%A, %d %b"),
        "why_choose_us": WHY_CHOOSE_US,
        "areas": areas,
        "faqs": FAQS,
        # ≤60 chars title — keyword + locale + brand
        "page_title": "Tiffin Service in Metcity, Yakubpur & Jhajjar",
        # ~150 chars meta description
        "page_description": (
            "Homemade veg tiffin service in Metcity, Yakubpur and Jhajjar. "
            "Daily tiffin ₹80, monthly plans from ₹2000, rice bowls and snacks. Order online."
        ),
        "jsonld_blobs": [seo.dump(j) for j in jsonld if j],
        "canonical_url": seo.canonical(request),
    }
    response = render(request, "tiffin/home.html", ctx)
    if not request.user.is_authenticated:
        _set_anonymous_cache(response)
    return response


def menu(request):
    site = SiteSettings.get()
    plans = list(visible_plans())
    areas = list(DeliveryArea.objects.filter(is_active=True))
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.website_jsonld(request, site),
        seo.breadcrumb_jsonld([
            ("Home", request.build_absolute_uri(reverse("home"))),
            ("Plans", request.build_absolute_uri(reverse("menu"))),
        ]),
    ]
    response = render(request, "tiffin/menu.html", {
        "plans": plans,
        # ≤60 chars
        "page_title": "Tiffin Plans & Prices in Jhajjar | ₹80 Veg Tiffin",
        # ~150 chars
        "page_description": (
            "See tiffin plans and prices for Metcity, Yakubpur and Jhajjar: "
            "₹80 daily tiffin, ₹2000 monthly single meal, ₹60 rice bowl and snacks."
        ),
        "jsonld_blobs": [seo.dump(j) for j in jsonld if j],
        "canonical_url": seo.canonical(request),
    })
    if not request.user.is_authenticated:
        _set_anonymous_cache(response)
    return response


def location_page(request, area_slug: str):
    area = SERVICE_AREAS.get(area_slug)
    if area is None:
        raise Http404("Unknown service area")

    lunch, dinner = _todays_menu()
    site = SiteSettings.get()
    plans = list(visible_plans())
    areas = list(DeliveryArea.objects.filter(is_active=True))
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.website_jsonld(request, site),
        seo.service_jsonld(request, site, area, plans),
        seo.breadcrumb_jsonld([
            ("Home", request.build_absolute_uri(reverse("home"))),
            (area["headline"], request.build_absolute_uri(reverse("location_page", args=[area_slug]))),
        ]),
    ]

    response = render(request, "tiffin/location.html", {
        "area": area,
        "area_slug": area_slug,
        "plans": plans,
        "todays_lunch": lunch,
        "todays_dinner": dinner,
        "page_title": area["title"],
        "page_description": area["description"],
        "jsonld_blobs": [seo.dump(j) for j in jsonld if j],
        "canonical_url": seo.canonical(request),
    })
    if not request.user.is_authenticated:
        _set_anonymous_cache(response)
    return response


@require_GET
def review_redirect(request):
    site = SiteSettings.get()
    target = site.google_business_url or site.google_maps_url or reverse("home")
    return redirect(target)


# ---------- SEO endpoints --------------------------------------------------

@require_GET
@cache_control(max_age=3600, public=True)
def robots_txt(request):
    site = SiteSettings.get()
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /django-admin/",
        "Disallow: /admin-orders/",
        "Disallow: /admin-login/",
        "Disallow: /admin-logout/",
        "Disallow: /order/success/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
    ])
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_http_methods(["GET", "POST"])
def order(request):
    plans = list(visible_plans())
    addons = list(Addon.objects.filter(is_active=True))
    now = timezone.localtime()

    initial = {}
    plan_slug = request.GET.get("plan")
    if plan_slug:
        try:
            selected_plan = visible_plans().get(slug=plan_slug)
            initial["plan"] = selected_plan.pk
            if selected_plan.category in {Plan.Category.RICE_BOWL, Plan.Category.SNACK}:
                initial["delivery_date"] = timezone.localdate()
        except Plan.DoesNotExist:
            pass
    # Preselect the first/cheapest active plan if none was requested.
    # Cuts one tap on a phone, and the user can change with one tap.
    if "plan" not in initial:
        default_plan = (
            visible_plans().order_by("sort_order", "price").first()
        )
        if default_plan:
            initial["plan"] = default_plan.pk
    meal_param = request.GET.get("meal")
    if meal_param in dict(Order.MealTime.choices):
        initial["meal_time"] = meal_param

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            new_order = form.save()
            return redirect("order_success", code=new_order.code)
    else:
        form = OrderForm(initial=initial)

    site = SiteSettings.get()
    areas = list(DeliveryArea.objects.filter(is_active=True))
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.website_jsonld(request, site),
        seo.breadcrumb_jsonld([
            ("Home", request.build_absolute_uri(reverse("home"))),
            ("Order Tiffin Online", request.build_absolute_uri(reverse("order"))),
        ]),
    ]

    return render(
        request,
        "tiffin/order_form.html",
        {
            "form": form,
            "plans": plans,
            "addons": addons,
            "order_today_iso": now.date().isoformat(),
            "order_current_minutes": _minutes_after_midnight(now.time()),
            "tiffin_lunch_cutoff_minutes": _minutes_after_midnight(TIFFIN_LUNCH_CUTOFF),
            "tiffin_dinner_cutoff_minutes": _minutes_after_midnight(TIFFIN_DINNER_CUTOFF),
            "max_delivery_km": MAX_DELIVERY_KM,
            "page_title": "Order Tiffin Online in Metcity | Ravinarayan Tiffin",
            "page_description": (
                "Order tiffin online in Metcity, Yakubpur and Jhajjar. Daily veg tiffin "
                "₹80, monthly plans from ₹2000, rice bowl ₹60 and group snacks."
            ),
            "jsonld_blobs": [seo.dump(j) for j in jsonld if j],
            "canonical_url": seo.canonical(request),
        },
    )


def order_success(request, code: str):
    order = get_object_or_404(Order, code=code)
    site = SiteSettings.get()

    # Build a rich WhatsApp message for the customer to send
    addon_lines = "\n".join(
        f"  + {a['name']} × {a['qty']} (₹{a['price'] * a['qty']})"
        for a in (order.addons or [])
    )
    addon_block = f"\n*Add-ons:*\n{addon_lines}" if addon_lines else ""

    plan_line = f"*Plan:* {order.plan_name} × {order.quantity}"
    if order.meal_multiplier > 1:
        plan_line += f" (Lunch + Dinner = {order.effective_meals} meals)"
    plan_line += " (price to confirm)" if order.plan_price_on_request else f" (₹{order.plan_subtotal})"
    known_total = order.addons_total + order.delivery_fee
    delivery_line = (
        f"*Delivery charge:* ₹{order.delivery_fee}"
        + (f" ({order.delivery_distance_km} km)" if order.delivery_distance_km is not None else "")
        + "\n"
        if order.delivery_method == Order.Method.DELIVERY else ""
    )

    if order.delivery_method == Order.Method.PICKUP:
        location_block = (
            f"*Method:* Pick up from counter\n"
            f"*Pickup at:* {site.address}\n"
            f"*Hours:* {site.hours}\n"
        )
    else:
        location_block = (
            f"*Method:* Home delivery\n"
            f"*Area:* {order.area}\n"
            f"*Address:* {order.address}\n"
            + (f"*Map:* {order.location_url}\n" if order.location_url else "")
            + delivery_line
        )

    msg = (
        f"Hi {site.short_name}, I just placed an order on your website.\n\n"
        f"*Order ID:* {order.code}\n"
        f"*Name:* {order.full_name}\n"
        f"*Phone:* {order.phone}\n\n"
        f"{plan_line}"
        f"{addon_block}\n\n"
        f"*Meal:* {order.get_meal_time_display()}\n"
        f"*Delivery date:* {order.delivery_date.isoformat()}\n"
        f"{location_block}"
        + (f"*Notes:* {order.notes}\n" if order.notes else "")
        + (
            f"\n*Total:* Price to confirm on WhatsApp"
            + (f" + ₹{known_total} fixed charges" if known_total else "")
            if order.plan_price_on_request else f"\n*Total:* ₹{order.total_price}"
        )
        + "\n\nPlease confirm. Thanks!"
    )
    wa_url = f"https://wa.me/{site.whatsapp_number}?text={quote(msg)}"

    return render(
        request,
        "tiffin/order_success.html",
        {"order": order, "wa_confirm_url": wa_url},
    )


# ---------- auth (custom login/logout) -------------------------------------

@require_http_methods(["GET", "POST"])
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_orders")

    error = None
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_staff:
            error = "Invalid username or password."
        else:
            auth_login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next") or reverse("admin_orders")
            # Avoid open-redirect: only allow same-origin paths
            if not next_url.startswith("/"):
                next_url = reverse("admin_orders")
            return redirect(next_url)

    return render(
        request,
        "tiffin/login.html",
        {"error": error, "next": request.GET.get("next", "")},
    )


@require_POST
def admin_logout(request):
    auth_logout(request)
    return redirect("home")


# ---------- staff-only admin orders ---------------------------------------

def _staff_required(view):
    return login_required(login_url="admin_login")(
        user_passes_test(lambda u: u.is_active and u.is_staff, login_url="admin_login")(view)
    )


@_staff_required
def admin_orders(request):
    qs = Order.objects.all()
    status_filter = request.GET.get("status", "")
    if status_filter in dict(Order.Status.choices):
        qs = qs.filter(status=status_filter)

    return render(
        request,
        "tiffin/admin_orders.html",
        {
            "orders": qs[:500],
            "status_choices": Order.Status.choices,
            "active_status": status_filter,
        },
    )


@_staff_required
@require_POST
def admin_update_status(request, code: str):
    order = get_object_or_404(Order, code=code)
    new_status = request.POST.get("status", "")
    if new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save(update_fields=["status"])
        messages.success(request, f"Order {order.code} updated to {order.get_status_display()}.")
    else:
        messages.error(request, "Invalid status.")
    return redirect("admin_orders")
