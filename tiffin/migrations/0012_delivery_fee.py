from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tiffin", "0011_monthly_plan_rate_3500")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivery_distance_km",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_fee",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
