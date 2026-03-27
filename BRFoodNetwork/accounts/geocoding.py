import json
import math
import re
import urllib.request
import urllib.parse

# Bristol city centre coordinates
BRISTOL_LAT = 51.4545
BRISTOL_LNG = -2.5879
MAX_RADIUS_MILES = 20


def _normalise_postcode(pc):
    """Insert a space before the last 3 characters of a UK postcode if missing."""
    pc = pc.strip().upper().replace(' ', '')
    if len(pc) >= 5:
        return pc[:-3] + ' ' + pc[-3:]
    return pc


def geocode_address(address, postal_code=''):
    """Convert a postal code to (latitude, longitude) using OpenStreetMap Nominatim.
    Uses only the postal code for reliability. Returns (lat, lng) or (None, None)."""
    postal_code = _normalise_postcode(postal_code) if postal_code else ''

    # Geocode by postcode only — more reliable than full address
    query = f"{postal_code}, UK" if postal_code else f"{address}, UK"
    params = urllib.parse.urlencode({
        'q': query,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'gb',
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'BRFoodNetwork/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass

    return None, None


def haversine(lat1, lon1, lat2, lon2):
    """Distance in miles between two GPS coordinate pairs."""
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_within_bristol_radius(lat, lng):
    """Check if coordinates are within 20 miles of Bristol city centre."""
    if lat is None or lng is None:
        return False
    return haversine(BRISTOL_LAT, BRISTOL_LNG, lat, lng) <= MAX_RADIUS_MILES
