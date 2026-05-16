from django.db import migrations, models


SEO_KEYWORDS = (
    "tiffin service, tiffin service in Metcity, tiffin service in Yakubpur, "
    "tiffin service near me, tiffin near me, homemade tiffin Metcity, "
    "veg tiffin service, daily tiffin service, monthly tiffin service, "
    "office lunch tiffin, PG tiffin service, dabba service Jhajjar, "
    "lunch tiffin, dinner tiffin, ghar ka khana"
)

SITE_DESCRIPTION = (
    "Fresh homemade veg tiffin service in Metcity, Yakubpur and Jhajjar. "
    "Daily tiffin ₹80, monthly lunch-only or dinner-only ₹2000, "
    "lunch+dinner ₹3500, rice bowl ₹60. Order online or WhatsApp."
)

MONTHLY_ITEMS = (
    "Lunch + Dinner daily\n4 Roti, Sabzi, Dal, Rice\nWeekly menu rotation\n"
    "1 special meal / week\nLunch-only or dinner-only: ₹2000/month"
)

MONTHLY_ITEMS_REVERSE = (
    "Lunch + Dinner daily\n4 Roti, Sabzi, Dal, Rice\nWeekly menu rotation\n"
    "1 special meal / week\nLunch-only or dinner-only: ₹1800/month"
)


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    Plan = apps.get_model("tiffin", "Plan")

    SiteSettings.objects.all().update(
        seo_keywords=SEO_KEYWORDS,
        site_description=SITE_DESCRIPTION,
    )
    Plan.objects.filter(slug="daily-tiffin").update(price=80)
    Plan.objects.filter(slug="pg-monthly").update(
        monthly_single_meal_price=2000,
        items=MONTHLY_ITEMS,
    )


def reverse(apps, schema_editor):
    Plan = apps.get_model("tiffin", "Plan")
    Plan.objects.filter(slug="daily-tiffin").update(price=70)
    Plan.objects.filter(slug="pg-monthly").update(
        monthly_single_meal_price=1800,
        items=MONTHLY_ITEMS_REVERSE,
    )


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0017_delivery_cap_and_bitmap_menu_assets")]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="seo_keywords",
            field=models.CharField(
                blank=True,
                default=SEO_KEYWORDS,
                help_text="Comma-separated keywords. Used in meta keywords + helps drive copy.",
                max_length=400,
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="site_description",
            field=models.CharField(
                blank=True,
                default=SITE_DESCRIPTION,
                help_text="160-300 chars. Used as the site-wide default meta description.",
                max_length=320,
            ),
        ),
        migrations.RunPython(forwards, reverse),
    ]
