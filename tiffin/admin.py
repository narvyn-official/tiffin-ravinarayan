from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from .models import Addon, DailyMenu, DeliveryArea, Order, Plan, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand", {"fields": ("business_name", "short_name", "tagline")}),
        ("Contact", {"fields": ("phone", "whatsapp_number", "email")}),
        ("Location & hours", {"fields": ("address", "hours")}),
        ("Delivery zone (geofence)", {
            "fields": ("delivery_center_lat", "delivery_center_lng", "delivery_radius_km"),
            "description": (
                "Set your kitchen's coordinates and an optional max delivery radius (km). "
                "Delivery is free up to 2 km, then ₹10 per started 2 km slab. "
                "Set radius to 0 or 2 for no hard cap; set a higher number to reject orders beyond it."
            ),
        }),
        ("Pickup", {"fields": ("pickup_enabled",)}),
        ("Social (optional)", {"fields": ("instagram_url", "facebook_url", "google_maps_url")}),
    )
    readonly_fields = ()

    # There can only be one — block "Add" and reroute "Add" to the singleton.
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        # Override the default changelist to redirect to the singleton change form.
        custom = [path("", self.admin_site.admin_view(self._open_singleton), name=f"{self.opts.app_label}_{self.opts.model_name}_changelist")]
        return custom + urls

    def _open_singleton(self, request):
        obj = SiteSettings.get()
        return redirect(f"./{obj.pk}/change/")


@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name",)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "price_on_request", "unit", "min_quantity", "available_day_of_week", "is_active", "sort_order")
    list_editable = ("price", "price_on_request", "is_active", "sort_order")
    list_filter = ("category", "is_active", "available_day_of_week")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "price", "unit", "is_active", "sort_order")
    list_editable = ("price", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ("get_day_of_week_display", "get_meal_time_display", "is_active")
    list_filter = ("day_of_week", "meal_time", "is_active")
    ordering = ("day_of_week", "meal_time")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "delivery_method", "full_name", "phone", "plan_name",
                    "quantity", "meal_time", "delivery_date", "total_price",
                    "status", "created_at")
    list_filter = ("status", "delivery_method", "meal_time", "area", "plan_slug")
    search_fields = ("code", "full_name", "phone", "address")
    list_editable = ("status",)
    readonly_fields = ("code", "created_at", "plan_name", "plan_price", "plan_price_on_request", "plan_unit",
                        "delivery_distance_km", "delivery_fee", "addons", "addons_total", "total_price", "location_url")
