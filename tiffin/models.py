"""
Models for Ravinarayan PG & Tiffin Service.

Everything that the owner needs to edit lives in the DB:
- SiteSettings (singleton): brand, contact, WhatsApp number
- DeliveryArea: areas the business serves
- Plan: tiffin plans (price, items, badge)
- Addon: chapati / raita / sweets / curd / lassi / etc
- DailyMenu: day-of-week × lunch/dinner items
- Order: customer orders (kept for owner's records)
"""
import secrets
import string

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# --- helpers ----------------------------------------------------------------

def _gen_order_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.translate(str.maketrans("", "", "O0I1"))
    return "TF-" + "".join(secrets.choice(alphabet) for _ in range(6))


def _split_lines(text: str) -> list[str]:
    """Split a textarea into a clean list of trimmed, non-empty lines."""
    if not text:
        return []
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# --- site-wide settings (singleton) ----------------------------------------

class SiteSettings(models.Model):
    """Single row of business-wide settings.

    Use SiteSettings.get() to fetch (auto-creates with defaults).
    """
    business_name = models.CharField(max_length=120, default="Ravinarayan PG & Tiffin Service")
    short_name = models.CharField(max_length=60, default="Ravinarayan Tiffin",
                                   help_text="Used in compact spots like the nav.")
    tagline = models.CharField(max_length=200, blank=True,
                               default="Fresh homemade tiffin, delivered daily.")

    phone = models.CharField(max_length=30, default="+91 98765 43210")
    whatsapp_number = models.CharField(
        max_length=20,
        default="919876543210",
        help_text="International format, digits only — no '+' or spaces. e.g. 919876543210",
    )
    email = models.EmailField(default="orders@ravinarayan.example")
    address = models.CharField(max_length=300, default="Metcity, Bahadurgarh, Jhajjar district, Haryana 124507")
    # Split address pieces for proper schema.org PostalAddress + local SEO
    city = models.CharField(max_length=80, default="Jhajjar")
    state = models.CharField(max_length=80, default="Haryana")
    postal_code = models.CharField(max_length=12, default="124507")
    country = models.CharField(max_length=80, default="India")
    country_code = models.CharField(max_length=2, default="IN", help_text="ISO 2-letter — e.g. IN, US.")
    hours = models.CharField(max_length=120, default="Mon – Sat, 10:00 AM – 9:00 PM")

    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True, help_text="Your Google Business Profile / maps listing URL.")
    google_business_url = models.URLField(blank=True, help_text="Your Google Business Profile sharable link.")

    # SEO / analytics
    ga_measurement_id = models.CharField(
        max_length=20, blank=True,
        help_text="Google Analytics 4 Measurement ID (e.g. G-XXXXXXXXXX). Leave blank to disable.",
    )
    seo_keywords = models.CharField(
        max_length=400, blank=True,
        default=(
            "tiffin service Jhajjar, tiffin in Metcity, tiffin in Yakubpur, "
            "tiffin Bahadurgarh, tiffin Farrukhnagar, homemade tiffin Haryana, "
            "monthly tiffin PG, lunch tiffin office, veg tiffin near me, "
            "dabba service Jhajjar, tiffin near me, ghar ka khana"
        ),
        help_text="Comma-separated keywords. Used in meta keywords + helps drive copy.",
    )
    site_description = models.CharField(
        max_length=320, blank=True,
        default=(
            "Fresh homemade veg tiffin service in Jhajjar — Metcity, Yakubpur, "
            "Bahadurgarh & Farrukhnagar. Daily lunch & dinner at ₹70 per meal or "
            "₹3200 per month. Lunch by 1 PM, dinner by 8:30 PM. FSSAI compliant. "
            "Order on WhatsApp."
        ),
        help_text="160-300 chars. Used as the site-wide default meta description.",
    )

    # --- Delivery zone (geofence) ---
    delivery_center_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Latitude of your kitchen / business hub. Leave blank to disable geofencing.",
    )
    delivery_center_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Longitude of your kitchen / business hub.",
    )
    delivery_radius_km = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Maximum delivery distance in km. 0 = no geofence (only the area dropdown is enforced).",
    )

    # --- Pickup option ---
    pickup_enabled = models.BooleanField(
        default=True,
        help_text="When on, customers can choose to pick up from the counter instead of delivery.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self) -> str:
        return self.business_name

    def save(self, *args, **kwargs):
        # Enforce singleton — pk is always 1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_url(self) -> str:
        return f"https://wa.me/{self.whatsapp_number}" if self.whatsapp_number else "#"


# --- delivery areas ---------------------------------------------------------

class DeliveryArea(models.Model):
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


# --- plans ------------------------------------------------------------------

class Plan(models.Model):
    UNIT_CHOICES = [
        ("per meal", "per meal"),
        ("per month", "per month"),
        ("per week", "per week"),
        ("per meal (10+ qty)", "per meal (10+ qty)"),
    ]

    slug = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=80)
    tagline = models.CharField(max_length=160, blank=True)
    price = models.PositiveIntegerField(help_text="In ₹.")
    unit = models.CharField(max_length=40, choices=UNIT_CHOICES, default="per meal")
    items = models.TextField(
        help_text="One line per item. e.g.\n4 Roti\nSabzi\nDal\nRice\nSalad",
    )
    badge = models.CharField(
        max_length=30, blank=True,
        help_text="Optional. e.g. 'Most Popular', 'Best Value'.",
    )
    image_filename = models.CharField(
        max_length=80, blank=True,
        help_text="Filename inside static/img/ — e.g. 'plan-daily.jpg'. Leave blank to use plan-<slug>.jpg.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self) -> str:
        return f"{self.name} (₹{self.price} {self.unit})"

    @property
    def items_list(self) -> list[str]:
        return _split_lines(self.items)

    @property
    def image_path(self) -> str:
        """Filename inside static/img/ — explicit if set, otherwise convention."""
        return self.image_filename or f"plan-{self.slug}.png"

    @property
    def image_path_webp(self) -> str:
        """WebP version of image_path (50–80% smaller). Same name, .webp ext."""
        base = self.image_path
        if base.lower().endswith((".png", ".jpg", ".jpeg")):
            return base.rsplit(".", 1)[0] + ".webp"
        return base


# --- addons -----------------------------------------------------------------

class Addon(models.Model):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=160, blank=True)
    price = models.PositiveIntegerField(help_text="In ₹ per unit.")
    unit = models.CharField(max_length=30, blank=True, default="each",
                            help_text="e.g. 'each', 'per piece', '200 ml'")
    icon = models.CharField(
        max_length=4, blank=True, default="🥘",
        help_text="Optional emoji shown next to the add-on (e.g. 🥣, 🫓, 🍮).",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return f"{self.name} (₹{self.price})"


# --- daily menu -------------------------------------------------------------

class DailyMenu(models.Model):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    MEAL_LUNCH = "lunch"
    MEAL_DINNER = "dinner"
    MEAL_CHOICES = [(MEAL_LUNCH, "Lunch"), (MEAL_DINNER, "Dinner")]

    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    meal_time = models.CharField(max_length=10, choices=MEAL_CHOICES)
    items = models.TextField(help_text="One item per line.")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("day_of_week", "meal_time")
        ordering = ("day_of_week", "meal_time")

    def __str__(self) -> str:
        return f"{self.get_day_of_week_display()} — {self.get_meal_time_display()}"

    @property
    def items_list(self) -> list[str]:
        return _split_lines(self.items)


# --- orders -----------------------------------------------------------------

class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class MealTime(models.TextChoices):
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"
        BOTH = "both", "Lunch + Dinner"

    class Method(models.TextChoices):
        DELIVERY = "delivery", "Home delivery"
        PICKUP = "pickup", "Pick up from counter"

    code = models.CharField(max_length=16, unique=True, editable=False, db_index=True)

    delivery_method = models.CharField(
        max_length=10, choices=Method.choices, default=Method.DELIVERY, db_index=True,
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    area = models.CharField(max_length=80, blank=True)

    plan_slug = models.CharField(max_length=60)
    plan_name = models.CharField(max_length=80)
    plan_price = models.PositiveIntegerField()
    plan_unit = models.CharField(max_length=40, blank=True,
                                  help_text="Snapshot of plan unit at order time (e.g. 'per meal').")

    quantity = models.PositiveIntegerField(default=1)
    meal_time = models.CharField(max_length=10, choices=MealTime.choices, default=MealTime.LUNCH)
    delivery_date = models.DateField()
    notes = models.CharField(max_length=300, blank=True)
    # Optional Google Maps link captured from the customer's device geolocation.
    location_url = models.URLField(max_length=300, blank=True)

    # Snapshot of selected add-ons: [{"name": "Curd", "price": 30, "qty": 2}, ...]
    addons = models.JSONField(default=list, blank=True)
    addons_total = models.PositiveIntegerField(default=0)
    total_price = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if not self.code:
            for _ in range(5):
                candidate = _gen_order_code()
                if not Order.objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
            else:
                raise RuntimeError("Could not generate a unique order code")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.code} — {self.full_name}"

    @property
    def meal_multiplier(self) -> int:
        """Lunch + dinner doubles the meal count for per-meal plans."""
        if self.meal_time == self.MealTime.BOTH and "per meal" in (self.plan_unit or ""):
            return 2
        return 1

    @property
    def effective_meals(self) -> int:
        return self.quantity * self.meal_multiplier

    @property
    def plan_subtotal(self) -> int:
        return self.plan_price * self.quantity * self.meal_multiplier
