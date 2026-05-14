from datetime import time

from django.db import migrations


RICE_BOWLS = [
    (0, "rice-bowl-monday-dal", "Monday Dal Rice Bowl", "Dal", "rice-bowl-monday.svg"),
    (1, "rice-bowl-tuesday-chhole", "Tuesday Chhole Rice Bowl", "Chhole", "rice-bowl-tuesday.svg"),
    (2, "rice-bowl-wednesday-rajma", "Wednesday Rajma Rice Bowl", "Rajma", "rice-bowl-wednesday.svg"),
    (3, "rice-bowl-thursday-soya-chaap", "Thursday Soya Chaap Rice Bowl", "Soya chaap", "rice-bowl-thursday.svg"),
    (4, "rice-bowl-friday-curry", "Friday Curry Rice Bowl", "Curry", "rice-bowl-friday.svg"),
    (5, "rice-bowl-saturday-mix-dal", "Saturday Mix Dal Rice Bowl", "Mix dal", "rice-bowl-saturday.svg"),
    (6, "rice-bowl-sunday-matar-paneer", "Sunday Matar Paneer Rice Bowl", "Matar paneer", "rice-bowl-sunday.svg"),
]

SNACKS = [
    ("samosa", "Samosa", "Crisp, hot samosas for groups and offices", "snack-samosa.svg", 20),
    ("bread", "Bread", "Fresh bread snack order for tea-time or groups", "snack-bread.svg", 21),
    ("burger", "Burger", "Veg burger order for groups and events", "snack-burger.svg", 22),
]


def forwards(apps, schema_editor):
    Plan = apps.get_model("tiffin", "Plan")

    Plan.objects.filter(slug="daily-tiffin").update(
        category="tiffin",
        min_quantity=1,
        price_on_request=False,
        order_start_time=None,
        order_cutoff_time=None,
        available_day_of_week=None,
        items="4 Roti\nSabzi\nDal\nRice\nSalad\nLunch orders close 10:30 AM\nDinner orders close 7:30 PM",
    )
    Plan.objects.filter(slug="pg-monthly").update(
        category="tiffin",
        price=3500,
        monthly_single_meal_price=1800,
        min_quantity=1,
        price_on_request=False,
        order_start_time=None,
        order_cutoff_time=None,
        available_day_of_week=None,
        items=(
            "Lunch + Dinner daily\n4 Roti, Sabzi, Dal, Rice\nWeekly menu rotation\n"
            "1 special meal / week\nLunch-only or dinner-only: ₹1800/month"
        ),
    )

    for day, slug, name, main, image in RICE_BOWLS:
        Plan.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "category": "rice_bowl",
                "tagline": f"Rice bowl + salad + {main}",
                "price": 60,
                "price_on_request": False,
                "monthly_single_meal_price": None,
                "unit": "per bowl",
                "min_quantity": 1,
                "available_day_of_week": day,
                "order_start_time": time(9, 0),
                "order_cutoff_time": time(21, 0),
                "items": f"Rice bowl\nSalad\n{main}\nAvailable 9 AM to 9 PM",
                "badge": "Daily Bowl",
                "image_filename": image,
                "is_active": True,
                "sort_order": 10 + day,
            },
        )

    for slug, name, tagline, image, sort_order in SNACKS:
        Plan.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "category": "snack",
                "tagline": tagline,
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
                "image_filename": image,
                "is_active": True,
                "sort_order": sort_order,
            },
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0014_order_plan_price_on_request_and_more")]

    operations = [migrations.RunPython(forwards, reverse)]
