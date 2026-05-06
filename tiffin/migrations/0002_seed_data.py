"""Seed initial business data so the site looks complete on first run.

Idempotent: only creates rows that don't exist yet. Owner can edit/delete
everything from /django-admin/ afterwards.
"""
from django.db import migrations


def seed(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    DeliveryArea = apps.get_model("tiffin", "DeliveryArea")
    Plan = apps.get_model("tiffin", "Plan")
    Addon = apps.get_model("tiffin", "Addon")
    DailyMenu = apps.get_model("tiffin", "DailyMenu")

    from tiffin.seed import (
        DEFAULT_AREAS, DEFAULT_PLANS, DEFAULT_ADDONS, DEFAULT_DAILY_MENU,
    )

    # Singleton site settings
    SiteSettings.objects.get_or_create(pk=1)

    # Areas
    for i, name in enumerate(DEFAULT_AREAS):
        DeliveryArea.objects.get_or_create(name=name, defaults={"sort_order": i})

    # Plans
    for p in DEFAULT_PLANS:
        Plan.objects.get_or_create(slug=p["slug"], defaults=p)

    # Add-ons
    for a in DEFAULT_ADDONS:
        Addon.objects.get_or_create(name=a["name"], defaults=a)

    # Daily menu
    for dow, meal, items in DEFAULT_DAILY_MENU:
        DailyMenu.objects.get_or_create(
            day_of_week=dow, meal_time=meal,
            defaults={"items": items, "is_active": True},
        )


def unseed(apps, schema_editor):
    # Reverse: do nothing. Don't wipe owner-edited data.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tiffin", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed, unseed),
    ]
