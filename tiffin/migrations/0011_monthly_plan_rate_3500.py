"""Update the PG Monthly Plan rate to 3500.

Keeps existing installs aligned with the current copy and model defaults.
"""
from django.db import migrations, models


OLD_RATE_TEXTS = ("₹3200", "₹3499")
NEW_RATE_TEXT = "₹3500"


def forwards(apps, schema_editor):
    Plan = apps.get_model("tiffin", "Plan")
    SiteSettings = apps.get_model("tiffin", "SiteSettings")

    Plan.objects.filter(slug="pg-monthly").update(price=3500)

    site = SiteSettings.objects.first()
    if site is not None and site.site_description:
        description = site.site_description
        for old in OLD_RATE_TEXTS:
            description = description.replace(old, NEW_RATE_TEXT)
        if description != site.site_description:
            site.site_description = description
            site.save(update_fields=["site_description"])


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0010_only_local_areas_active")]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="site_description",
            field=models.CharField(
                blank=True,
                default=(
                    "Fresh homemade veg tiffin service in Jhajjar — Metcity, Yakubpur, "
                    "Bahadurgarh & Farrukhnagar. Daily lunch & dinner at ₹70 per meal or "
                    "₹3500 per month. Lunch by 1 PM, dinner by 8:30 PM. FSSAI compliant. "
                    "Order on WhatsApp."
                ),
                help_text="160-300 chars. Used as the site-wide default meta description.",
                max_length=320,
            ),
        ),
        migrations.RunPython(forwards, reverse),
    ]
