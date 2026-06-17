from django.db import migrations, models


SEO_KEYWORDS = (
    "tiffin service, tiffin service near me, tiffin service in Metcity, "
    "tiffin service in Yakubpur, tiffin service in Jhajjar, homemade tiffin service, "
    "veg tiffin service, monthly tiffin service, daily tiffin service, "
    "lunch tiffin service, dinner tiffin service, PG tiffin service, "
    "office lunch tiffin, dabba service, ghar ka khana"
)

SITE_DESCRIPTION = (
    "Homemade veg tiffin service in Metcity, Yakubpur and Jhajjar. Daily tiffin "
    "₹80, monthly plans from ₹2000, lunch and dinner delivery, rice bowls and snacks. "
    "Order online."
)

GOOGLE_MAPS_URL = "https://www.google.com/maps?cid=16202019902653058804"

ACTIVE_AREAS = [
    ("Metcity", 1),
    ("Yakubpur", 2),
    ("Jhajjar", 3),
]


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    DeliveryArea = apps.get_model("tiffin", "DeliveryArea")

    SiteSettings.objects.all().update(
        business_name="Ravinarayan PG & Tiffin Services",
        address="7A, Yakubpur, Jhajjar, Haryana 124103",
        city="Jhajjar",
        state="Haryana",
        postal_code="124103",
        country="India",
        country_code="IN",
        google_maps_url=GOOGLE_MAPS_URL,
        google_business_url=GOOGLE_MAPS_URL,
        seo_keywords=SEO_KEYWORDS,
        site_description=SITE_DESCRIPTION,
        delivery_center_lat="28.484427",
        delivery_center_lng="76.784015",
        delivery_radius_km=4,
    )

    active_names = [name for name, _ in ACTIVE_AREAS]
    DeliveryArea.objects.exclude(name__in=active_names).update(is_active=False)
    for name, sort_order in ACTIVE_AREAS:
        DeliveryArea.objects.update_or_create(
            name=name,
            defaults={"is_active": True, "sort_order": sort_order},
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0018_pricing_and_local_seo")]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="business_name",
            field=models.CharField(default="Ravinarayan PG & Tiffin Services", max_length=120),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="address",
            field=models.CharField(default="7A, Yakubpur, Jhajjar, Haryana 124103", max_length=300),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="postal_code",
            field=models.CharField(default="124103", max_length=12),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="google_maps_url",
            field=models.URLField(
                blank=True,
                default=GOOGLE_MAPS_URL,
                help_text="Your Google Business Profile / maps listing URL.",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="google_business_url",
            field=models.URLField(
                blank=True,
                default=GOOGLE_MAPS_URL,
                help_text="Your Google Business Profile sharable link.",
            ),
        ),
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
        migrations.AlterField(
            model_name="sitesettings",
            name="delivery_center_lat",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                default="28.484427",
                help_text="Latitude of your kitchen / business hub. Leave blank to disable geofencing.",
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="delivery_center_lng",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                default="76.784015",
                help_text="Longitude of your kitchen / business hub.",
                max_digits=9,
                null=True,
            ),
        ),
        migrations.RunPython(forwards, reverse),
    ]
