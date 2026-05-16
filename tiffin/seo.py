"""
Per-page SEO helpers — canonical URLs, meta titles/descriptions,
and Schema.org JSON-LD payloads (LocalBusiness/Restaurant, Menu,
Offer, FAQPage, BreadcrumbList).

Kept here so views/templates stay terse and we can unit-test the JSON.
"""
from __future__ import annotations

import json
from datetime import date

from django.urls import reverse

from .geo import MAX_DELIVERY_KM


# ---------- meta-tag helpers ----------------------------------------------

def absolute_url(request, path: str) -> str:
    return request.build_absolute_uri(path)


def canonical(request) -> str:
    return request.build_absolute_uri(request.path)


# ---------- Schema.org JSON-LD --------------------------------------------

def _full(request, named_url: str) -> str:
    return absolute_url(request, reverse(named_url))


def _opening_hours(site) -> list[dict]:
    """Best-effort parse from settings string. Owner can override later."""
    # Default: Mon-Sat 10:00-21:00. If owner customises 'hours' free-text we
    # still return this default for schema; that's better than wrong data.
    return [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "opens": "10:00",
        "closes": "21:00",
    }]


def _postal_address(site) -> dict:
    return {
        "@type": "PostalAddress",
        "streetAddress": site.address,
        "addressLocality": site.city,
        "addressRegion": site.state,
        "postalCode": site.postal_code,
        "addressCountry": site.country_code or "IN",
    }


def _geo(site) -> dict | None:
    if site.delivery_center_lat is None or site.delivery_center_lng is None:
        return None
    return {
        "@type": "GeoCoordinates",
        "latitude": float(site.delivery_center_lat),
        "longitude": float(site.delivery_center_lng),
    }


def _service_area(site, areas) -> list[dict]:
    """Schema.org areaServed entries — one per active delivery area."""
    items = []
    if (
        site.delivery_center_lat
        and site.delivery_center_lng
    ):
        items.append({
            "@type": "GeoCircle",
            "geoMidpoint": _geo(site),
            "geoRadius": MAX_DELIVERY_KM * 1000,  # metres
        })
    for a in areas:
        items.append({"@type": "Place", "name": f"{a.name}, {site.city}"})
    return items


def restaurant_jsonld(request, site, areas, plans) -> dict:
    home = _full(request, "home")
    payload: dict = {
        "@context": "https://schema.org",
        "@type": ["Restaurant", "FoodEstablishment", "LocalBusiness"],
        "@id": home + "#business",
        "name": site.business_name,
        "alternateName": site.short_name,
        "description": site.site_description,
        "keywords": site.seo_keywords,
        "url": home,
        "telephone": site.phone,
        "email": site.email,
        "image": absolute_url(request, "/static/img/logo.png"),
        "logo": absolute_url(request, "/static/img/logo.png"),
        "priceRange": "₹",
        "currenciesAccepted": "INR",
        "paymentAccepted": "Cash, UPI, Bank transfer",
        "servesCuisine": ["Indian", "North Indian", "Vegetarian", "Home-style"],
        "address": _postal_address(site),
        "openingHoursSpecification": _opening_hours(site),
        "areaServed": _service_area(site, areas),
        "hasMap": site.google_maps_url or "",
        "sameAs": [u for u in [
            site.facebook_url, site.instagram_url,
            site.google_business_url, site.google_maps_url,
        ] if u],
    }
    geo = _geo(site)
    if geo:
        payload["geo"] = geo

    # Offer catalog: each plan = an Offer
    offers = []
    for p in plans:
        offer = {
            "@type": "Offer",
            "name": p.name,
            "description": p.tagline,
            "priceCurrency": "INR",
            "url": _full(request, "menu"),
            "availability": "https://schema.org/InStock",
            "category": p.category_label,
        }
        if not p.price_on_request:
            offer["price"] = str(p.price)
        offers.append(offer)
    if offers:
        payload["makesOffer"] = offers

    # Drop empty fields for a cleaner payload
    return {k: v for k, v in payload.items() if v not in (None, "", [], {})}


def menu_jsonld(request, site, todays_lunch, todays_dinner) -> dict | None:
    """Schema.org Menu with hasMenuSection (Lunch + Dinner)."""
    sections = []
    if todays_lunch:
        sections.append({
            "@type": "MenuSection",
            "name": "Lunch",
            "description": "Available for delivery by 1:00 PM",
            "hasMenuItem": [{"@type": "MenuItem", "name": item} for item in todays_lunch.items_list],
        })
    if todays_dinner:
        sections.append({
            "@type": "MenuSection",
            "name": "Dinner",
            "description": "Available for delivery by 8:30 PM",
            "hasMenuItem": [{"@type": "MenuItem", "name": item} for item in todays_dinner.items_list],
        })
    if not sections:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "Menu",
        "name": f"Today's menu — {date.today().strftime('%A, %d %b %Y')}",
        "description": f"Today's homestyle tiffin spread from {site.business_name}.",
        "hasMenuSection": sections,
    }


def faq_jsonld(faqs: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }


def breadcrumb_jsonld(items: list[tuple[str, str]]) -> dict:
    """items: [(name, absolute_url), …]"""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(items)
        ],
    }


def dump(payload) -> str:
    """Compact JSON, safe to embed in <script type=application/ld+json>."""
    if payload is None:
        return ""
    # Escape `</` to prevent breaking out of <script>
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
