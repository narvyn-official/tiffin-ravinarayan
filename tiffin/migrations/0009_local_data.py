"""Sync existing prod rows to the new Jhajjar / Haryana local context.

Conservative — only overwrites SiteSettings fields that still hold the old
Pune defaults, so an owner who already customised their data in admin
won't have it clobbered.

Idempotent for DeliveryArea: ensures Metcity, Yakubpur, Bahadurgarh and
Farrukhnagar exist and are active.
"""
from django.db import migrations


# Old Pune-era defaults that we can safely overwrite. Anything else means
# the owner customised it and we should leave it alone.
PUNE_DEFAULTS = {
    "city": "Pune",
    "state": "Maharashtra",
    "postal_code": "411001",
    "address": "Shop 12, Market Road, Pune 411001",
}

NEW_LOCAL = {
    "city": "Jhajjar",
    "state": "Haryana",
    "postal_code": "124507",
    "address": "Metcity, Bahadurgarh, Jhajjar district, Haryana 124507",
}

LOCAL_AREAS = [
    {"name": "Metcity",      "is_active": True, "sort_order": 1},
    {"name": "Yakubpur",     "is_active": True, "sort_order": 2},
    {"name": "Bahadurgarh",  "is_active": True, "sort_order": 3},
    {"name": "Farrukhnagar", "is_active": True, "sort_order": 4},
]


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    DeliveryArea = apps.get_model("tiffin", "DeliveryArea")

    site = SiteSettings.objects.first()
    if site is not None:
        changed = False
        for field, old_value in PUNE_DEFAULTS.items():
            if getattr(site, field, None) == old_value:
                setattr(site, field, NEW_LOCAL[field])
                changed = True
        if changed:
            site.save()

    # Make sure the local delivery areas exist & are active.
    for spec in LOCAL_AREAS:
        DeliveryArea.objects.update_or_create(
            name=spec["name"],
            defaults={"is_active": spec["is_active"], "sort_order": spec["sort_order"]},
        )


def reverse(apps, schema_editor):
    pass  # no-op; we don't restore Pune defaults


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0008_local_jhajjar")]
    operations = [migrations.RunPython(forwards, reverse)]
