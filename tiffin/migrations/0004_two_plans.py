"""Replace the original 5 default plans with the owner's 2 plans.

Idempotent — safe to re-run, only touches default-slug rows.
"""
from django.db import migrations


NEW_PLANS = [
    {
        "slug": "daily-tiffin",
        "name": "Daily Tiffin",
        "tagline": "Fresh, homestyle meal — order any day",
        "price": 70,
        "unit": "per meal",
        "items": "4 Roti\nSabzi\nDal\nRice\nSalad",
        "badge": "Most Popular",
        "image_filename": "plan-daily.png",
        "sort_order": 1,
    },
    {
        "slug": "pg-monthly",
        "name": "PG Monthly Plan",
        "tagline": "30 days of meals — best value for PGs, students & working professionals",
        "price": 3200,
        "unit": "per month",
        "items": "Lunch + Dinner daily\n4 Roti, Sabzi, Dal, Rice\nWeekly menu rotation\n1 special meal / week",
        "badge": "Best Value",
        "image_filename": "plan-monthly.png",
        "sort_order": 2,
    },
]

# Slugs that the original 0002 seed inserted but we no longer want.
OLD_DEFAULT_SLUGS_TO_REMOVE = [
    "regular-veg",
    "premium-veg",
    "office-lunch",
    "corporate-bulk",
]


def update(apps, schema_editor):
    Plan = apps.get_model("tiffin", "Plan")
    Plan.objects.filter(slug__in=OLD_DEFAULT_SLUGS_TO_REMOVE).delete()
    for p in NEW_PLANS:
        Plan.objects.update_or_create(
            slug=p["slug"],
            defaults={**p, "is_active": True},
        )


def revert(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0003_plan_image")]
    operations = [migrations.RunPython(update, revert)]
