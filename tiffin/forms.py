import re
from datetime import date, timedelta

from django import forms

from .geo import extract_coords, haversine_km
from .models import Addon, DeliveryArea, Order, Plan, SiteSettings

PHONE_RE = re.compile(r"^[0-9+\-\s]{7,20}$")

ALLOWED_MAP_PREFIXES = (
    "https://maps.google.com/",
    "https://www.google.com/maps",
    "https://goo.gl/maps/",
    "https://maps.app.goo.gl/",
)


class OrderForm(forms.ModelForm):
    """
    Order form bound to DB-driven plans, areas and add-ons.
    Add-on quantities are parsed from POST in clean(); each addon has its
    own number input rendered manually so we can lay them out as cards.
    """

    plan = forms.ModelChoiceField(
        queryset=Plan.objects.none(),
        widget=forms.HiddenInput(),
        required=True,
        error_messages={"required": "Please choose a plan."},
    )
    area = forms.ModelChoiceField(
        queryset=DeliveryArea.objects.none(),
        widget=forms.Select(attrs={"class": "field"}),
        empty_label="Select your area…",
        required=False,  # not required for pickup
    )
    delivery_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "field"}),
    )
    quantity = forms.IntegerField(
        min_value=1, max_value=100, initial=1,
        widget=forms.NumberInput(attrs={
            "class": "field qty-input", "inputmode": "numeric",
            "min": 1, "max": 100, "step": 1,
        }),
    )
    delivery_method = forms.ChoiceField(
        choices=Order.Method.choices,
        widget=forms.RadioSelect(attrs={"class": "method-radio"}),
        initial=Order.Method.DELIVERY,
    )

    class Meta:
        model = Order
        fields = [
            "delivery_method",
            "full_name",
            "phone",
            "address",
            "area",
            "quantity",
            "meal_time",
            "delivery_date",
            "notes",
            "location_url",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "field", "placeholder": "Your full name", "autocomplete": "name", "maxlength": 100}),
            "phone": forms.TextInput(attrs={"class": "field", "placeholder": "10-digit mobile number", "autocomplete": "tel", "inputmode": "tel"}),
            "address": forms.Textarea(attrs={"class": "field", "rows": 3, "placeholder": "Flat / building / street / landmark", "maxlength": 500}),
            "meal_time": forms.Select(attrs={"class": "field"}),
            "notes": forms.TextInput(attrs={"class": "field", "placeholder": "Less spicy, no onion, extra roti…", "maxlength": 300}),
            "location_url": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = Plan.objects.filter(is_active=True)
        self.fields["area"].queryset = DeliveryArea.objects.filter(is_active=True)
        if not self.is_bound:
            self.fields["delivery_date"].initial = date.today() + timedelta(days=1)

        # Hide pickup option entirely if disabled by owner
        site = SiteSettings.get()
        if not site.pickup_enabled:
            self.fields["delivery_method"].choices = [
                (Order.Method.DELIVERY, "Home delivery"),
            ]

        self.addons = list(Addon.objects.filter(is_active=True))
        self._addon_qty: dict[int, int] = {}

    # --- field cleaners --------------------------------------------------

    def clean_full_name(self):
        v = (self.cleaned_data.get("full_name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return v

    def clean_phone(self):
        v = (self.cleaned_data.get("phone") or "").strip()
        if not PHONE_RE.match(v):
            raise forms.ValidationError("Enter a valid phone number (digits, spaces, +, - only).")
        if len(re.sub(r"\D", "", v)) < 10:
            raise forms.ValidationError("Phone number is too short.")
        return v

    def clean_quantity(self):
        q = self.cleaned_data.get("quantity") or 0
        if q < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        if q > 100:
            raise forms.ValidationError("For orders above 100, please contact us directly.")
        return q

    def clean_location_url(self):
        url = (self.cleaned_data.get("location_url") or "").strip()
        if not url:
            return ""
        if not url.startswith(ALLOWED_MAP_PREFIXES):
            raise forms.ValidationError("Please paste a Google Maps link (must start with maps.google.com or maps.app.goo.gl).")
        if len(url) > 300:
            raise forms.ValidationError("Map URL too long.")
        return url

    def clean_delivery_date(self):
        d = self.cleaned_data.get("delivery_date")
        today = date.today()
        if not d:
            raise forms.ValidationError("Please pick a delivery date.")
        if d < today:
            raise forms.ValidationError("Delivery date cannot be in the past.")
        if d > today + timedelta(days=60):
            raise forms.ValidationError("Please pick a date within the next 60 days.")
        return d

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("delivery_method") or Order.Method.DELIVERY
        site = SiteSettings.get()

        # --- Address / area requirement depends on method ------------------
        if method == Order.Method.DELIVERY:
            if not (cleaned.get("address") or "").strip() or len((cleaned.get("address") or "").strip()) < 8:
                self.add_error("address", "Please enter a complete delivery address.")
            if not cleaned.get("area"):
                self.add_error("area", "Please choose a delivery area.")

            # --- Geofence check ---------------------------------------------
            url = cleaned.get("location_url") or ""
            if (
                site.delivery_center_lat is not None
                and site.delivery_center_lng is not None
                and float(site.delivery_radius_km) > 0
                and url
            ):
                coords = extract_coords(url)
                if coords:
                    dist = haversine_km(
                        coords[0], coords[1],
                        float(site.delivery_center_lat), float(site.delivery_center_lng),
                    )
                    radius = float(site.delivery_radius_km)
                    if dist > radius:
                        raise forms.ValidationError(
                            f"Sorry — delivery is not available at this location. "
                            f"It's {dist:.1f} km from our kitchen, but we deliver only within {radius:.0f} km. "
                            f"You can choose 'Pick up from counter' instead."
                        )
        else:  # pickup
            # Address & area aren't required; clear them if empty
            cleaned["address"] = (cleaned.get("address") or "").strip()
            # Area can be blank for pickup
            self._errors.pop("address", None)
            self._errors.pop("area", None)

        # --- Parse addon quantities from POST ------------------------------
        data = self.data
        for a in self.addons:
            raw = (data.get(f"addon_qty_{a.id}") or "0").strip()
            try:
                qty = int(raw)
            except ValueError:
                qty = 0
            if qty < 0:
                qty = 0
            if qty > 100:
                self.add_error(None, f"Too many of {a.name} (max 100).")
                qty = 0
            self._addon_qty[a.id] = qty
        return cleaned

    # --- save ------------------------------------------------------------

    def save(self, commit=True):
        order: Order = super().save(commit=False)
        plan: Plan = self.cleaned_data["plan"]
        area = self.cleaned_data.get("area")

        order.plan_slug = plan.slug
        order.plan_name = plan.name
        order.plan_price = plan.price
        order.plan_unit = plan.unit
        order.area = area.name if area else ""

        # Build addon snapshot
        addons_snapshot = []
        addons_total = 0
        for a in self.addons:
            qty = self._addon_qty.get(a.id, 0)
            if qty > 0:
                addons_snapshot.append({"name": a.name, "price": a.price, "qty": qty, "unit": a.unit})
                addons_total += a.price * qty

        order.addons = addons_snapshot
        order.addons_total = addons_total

        # Compute subtotal with multiplier (lunch+dinner doubles per-meal plans)
        multiplier = 2 if order.meal_time == Order.MealTime.BOTH and "per meal" in plan.unit else 1
        plan_subtotal = plan.price * order.quantity * multiplier
        order.total_price = plan_subtotal + addons_total

        if commit:
            order.save()
        return order
