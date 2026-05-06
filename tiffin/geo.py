"""Geometry helpers — coords parsing + haversine distance."""
import math
import re

# Match `?q=lat,lng`, `&q=lat,lng`, `@lat,lng,zoom`, `?ll=lat,lng`, `&center=lat,lng`
COORD_RE = re.compile(
    r"[?&@](?:q=|ll=|center=|loc=)?(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)"
)


def extract_coords(url: str) -> tuple[float, float] | None:
    """Pull (lat, lng) out of a Google Maps URL. Returns None if not present.

    Handles common forms:
      https://maps.google.com/?q=18.5912,73.7389
      https://www.google.com/maps/place/Foo/@18.5912,73.7389,15z
      https://www.google.com/maps?ll=18.5912,73.7389
    Shortened URLs (goo.gl/maps, maps.app.goo.gl) don't include coords inline,
    so we'll return None — caller should treat that as "geofence skipped".
    """
    if not url:
        return None
    m = COORD_RE.search(url)
    if not m:
        return None
    try:
        lat = float(m.group(1))
        lng = float(m.group(2))
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0  # km
    lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
