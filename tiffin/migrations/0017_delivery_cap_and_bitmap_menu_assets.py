from django.db import migrations, models


RICE_BOWL_IMAGES = {
    "rice-bowl-monday-dal": "rice-bowl-monday-dal.webp",
    "rice-bowl-tuesday-chhole": "rice-bowl-tuesday-chhole.webp",
    "rice-bowl-wednesday-rajma": "rice-bowl-wednesday-rajma.webp",
    "rice-bowl-thursday-soya-chaap": "rice-bowl-thursday-soya-chaap.webp",
    "rice-bowl-friday-curry": "rice-bowl-friday-curry.webp",
    "rice-bowl-saturday-mix-dal": "rice-bowl-saturday-mix-dal.webp",
    "rice-bowl-sunday-matar-paneer": "rice-bowl-sunday-matar-paneer.webp",
}

SNACKS = [
    (
        "samosa",
        {
            "name": "Samosa",
            "tagline": "Crisp, hot samosas for groups and offices",
            "image_filename": "snack-samosa.webp",
            "sort_order": 20,
        },
    ),
    (
        "bread-pakora",
        {
            "name": "Bread Pakora",
            "tagline": "Fresh bread pakora order for tea-time or groups",
            "image_filename": "snack-bread-pakora.webp",
            "sort_order": 21,
        },
    ),
    (
        "burger",
        {
            "name": "Burger",
            "tagline": "Veg burger order for groups and events",
            "image_filename": "snack-burger.webp",
            "sort_order": 22,
        },
    ),
]


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    Plan = apps.get_model("tiffin", "Plan")

    SiteSettings.objects.all().update(delivery_radius_km=4)

    for slug, image in RICE_BOWL_IMAGES.items():
        Plan.objects.filter(slug=slug).update(image_filename=image)

    if Plan.objects.filter(slug="bread").exists():
        if Plan.objects.filter(slug="bread-pakora").exists():
            Plan.objects.filter(slug="bread").update(is_active=False)
        else:
            Plan.objects.filter(slug="bread").update(slug="bread-pakora")

    for slug, values in SNACKS:
        defaults = {
            "category": "snack",
            "price": 0,
            "price_on_request": True,
            "monthly_single_meal_price": None,
            "unit": "price on request",
            "min_quantity": 15,
            "available_day_of_week": None,
            "order_start_time": None,
            "order_cutoff_time": None,
            "items": "Minimum order 15 pcs\nPrepared on order\nFinal price confirmed on WhatsApp",
            "badge": "On Order",
            "is_active": True,
            **values,
        }
        Plan.objects.update_or_create(slug=slug, defaults=defaults)


def reverse(apps, schema_editor):
    SiteSettings = apps.get_model("tiffin", "SiteSettings")
    SiteSettings.objects.all().update(delivery_radius_km=0)


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0016_alter_sitesettings_site_description")]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="delivery_radius_km",
            field=models.DecimalField(
                decimal_places=2,
                default=4,
                help_text=(
                    "Maximum delivery distance in km. Delivery is available up to 4 km only; "
                    "free up to 2 km, then ₹10 per started 2 km slab."
                ),
                max_digits=5,
            ),
        ),
        migrations.RunPython(forwards, reverse),
    ]
