"""Deactivate every DeliveryArea except the actual service zones.

The owner serves only Metcity and Yakubpur (Jhajjar district, Haryana) —
the rest of the seeded list is leftover from earlier defaults. Deactivate
(don't delete) so they're easy to re-enable from /django-admin/ if needed.
"""
from django.db import migrations


ACTIVE_NAMES = ["Metcity", "Yakubpur"]


def forwards(apps, schema_editor):
    DeliveryArea = apps.get_model("tiffin", "DeliveryArea")

    # Make sure both required areas exist
    for i, name in enumerate(ACTIVE_NAMES, start=1):
        DeliveryArea.objects.update_or_create(
            name=name,
            defaults={"is_active": True, "sort_order": i},
        )

    # Deactivate everything else
    DeliveryArea.objects.exclude(name__in=ACTIVE_NAMES).update(is_active=False)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0009_local_data")]
    operations = [migrations.RunPython(forwards, reverse)]
