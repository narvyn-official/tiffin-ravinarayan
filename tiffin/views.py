from datetime import date
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import seo
from .forms import OrderForm
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
        "₹70 per meal for the Daily Tiffin (4 roti, sabzi, dal, rice, salad). For long-term "
        "subscribers, our PG Monthly Plan is ₹3200 per month — works out to a big saving over "
        "ordering daily."
    ),
    (
        "Do you deliver near me?",
        "We currently deliver in Metcity, Yakubpur, Bahadurgarh and Farrukhnagar (Jhajjar district, "
        "Haryana). On the order page, tap 'Set delivery location', search for your address or use "
        "GPS — the map will show whether you're inside our delivery circle. If you're outside, you "
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
    {"icon": "₹",  "title": "Affordable", "text": "Honest pricing. No hidden charges in listed areas."},
    {"icon": "⏱", "title": "On Time", "text": "Lunch by 1 PM, dinner by 8:30 PM — every day."},
    {"icon": "❤️", "title": "Homestyle Taste", "text": "Less oil, balanced spice — like ghar ka khaana."},
    {"icon": "📞", "title": "Easy to Order", "text": "Order on WhatsApp or in 30 seconds on this site."},
]


def _todays_menu():
    """One query for both meals, cheaper than two filtered .first() calls."""
    dow = date.today().weekday()
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


# ---------- public pages ----------------------------------------------------

def home(request):
    lunch, dinner = _todays_menu()
    site = SiteSettings.get()
    plans = list(Plan.objects.filter(is_active=True))
    areas = list(DeliveryArea.objects.filter(is_active=True))

    # JSON-LD for SEO: a restaurant snippet, today's menu, and an FAQ page
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.faq_jsonld(FAQS),
    ]
    menu_payload = seo.menu_jsonld(request, site, lunch, dinner)
    if menu_payload:
        jsonld.append(menu_payload)

    # Names of active areas, used in concise meta description.
    area_names = ", ".join(a.name for a in areas[:3])
    ctx = {
        "plans": plans,
        "todays_lunch": lunch,
        "todays_dinner": dinner,
        "today_label": date.today().strftime("%A, %d %b"),
        "why_choose_us": WHY_CHOOSE_US,
        "areas": areas,
        "faqs": FAQS,
        # ≤60 chars title — keyword + locale + brand
        "page_title": (
            f"Tiffin Service in {site.city}"
            f"{' — ' + area_names if area_names else ''} | {site.short_name}"
        ),
        # ~150 chars meta description
        "page_description": (
            f"Fresh homemade veg tiffin in {site.city}"
            f"{' (' + area_names + ')' if area_names else ''}. ₹70 per meal or ₹3200/month. "
            f"Hot, hygienic, FSSAI compliant. Order on WhatsApp."
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
    plans = list(Plan.objects.filter(is_active=True))
    areas = list(DeliveryArea.objects.filter(is_active=True))
    jsonld = [
        seo.restaurant_jsonld(request, site, areas, plans),
        seo.breadcrumb_jsonld([
            ("Home", request.build_absolute_uri(reverse("home"))),
            ("Plans", request.build_absolute_uri(reverse("menu"))),
        ]),
    ]
    response = render(request, "tiffin/menu.html", {
        "plans": plans,
        # ≤60 chars
        "page_title": f"Tiffin Plans — ₹70 / meal · ₹3200 / month | {site.short_name}",
        # ~150 chars
        "page_description": (
            f"Two simple tiffin plans: Daily Tiffin at ₹70 per meal and PG Monthly at "
            f"₹3200/month. Fresh, homemade vegetarian meals — delivered in {site.city}."
        ),
        "jsonld_blobs": [seo.dump(j) for j in jsonld if j],
        "canonical_url": seo.canonical(request),
    })
    if not request.user.is_authenticated:
        _set_anonymous_cache(response)
    return response


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
    plans = list(Plan.objects.filter(is_active=True))
    addons = list(Addon.objects.filter(is_active=True))

    initial = {}
    plan_slug = request.GET.get("plan")
    if plan_slug:
        try:
            initial["plan"] = Plan.objects.get(slug=plan_slug, is_active=True).pk
        except Plan.DoesNotExist:
            pass
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

    return render(
        request,
        "tiffin/order_form.html",
        {
            "form": form,
            "plans": plans,
            "addons": addons,
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
    plan_line += f" (₹{order.plan_subtotal})"

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
        + f"\n*Total:* ₹{order.total_price}\n\nPlease confirm. Thanks!"
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
