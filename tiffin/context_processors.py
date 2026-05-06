from .models import DeliveryArea, SiteSettings


def business_info(request):
    """Expose site settings, delivery areas and the WhatsApp URL to every template."""
    try:
        site = SiteSettings.get()
        areas = DeliveryArea.objects.filter(is_active=True)
    except Exception:
        # Migrations haven't run yet — keep templates from crashing.
        return {"SITE": None, "AREAS": [], "WHATSAPP_URL": "#"}
    return {
        "SITE": site,
        "AREAS": areas,
        "WHATSAPP_URL": site.whatsapp_url,
    }
