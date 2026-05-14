from django.db.models import Q
from django.utils import timezone

from .models import Plan


def visible_plans(for_date=None):
    """Active plans, with only today's rice bowl shown."""
    day = (for_date or timezone.localdate()).weekday()
    return (
        Plan.objects.filter(is_active=True)
        .filter(
            Q(category=Plan.Category.RICE_BOWL, available_day_of_week=day)
            | ~Q(category=Plan.Category.RICE_BOWL)
        )
        .order_by("sort_order", "id")
    )
