import json
import math
import os
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


def get_driving_distance(lat1, lng1, lat2, lng2):
    """
    Return driving distance (miles) and duration (minutes) between two points
    by calling the API gateway's /distance endpoint.
    Falls back to straight-line haversine if the gateway is unreachable or
    the Google key is not configured.
    Result: {"distance_miles": float, "duration_minutes": float|None, "source": str}
    """
    gateway_url = os.getenv('API_GATEWAY_URL', '')
    if gateway_url:
        try:
            params = urllib.parse.urlencode({
                'origin_lat': lat1, 'origin_lng': lng1,
                'dest_lat': lat2, 'dest_lng': lng2,
            })
            req = urllib.request.Request(
                f"{gateway_url}/distance?{params}",
                headers={'User-Agent': 'BRFoodNetwork/1.0'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            pass
    # Fallback
    return {'distance_miles': haversine(lat1, lng1, lat2, lng2), 'duration_minutes': None, 'source': 'haversine'}


def get_driving_distances_batch(origin_lat, origin_lng, destinations):
    """
    Return driving distances from one origin to multiple destinations in a
    single API gateway call (Google Distance Matrix batch request).
    destinations: list of {"lat": float, "lng": float}
    Returns a list of {"distance_miles": float, "duration_minutes": float|None, "source": str}
    in the same order as destinations.  Falls back to haversine on failure.
    """
    if not destinations:
        return []
    gateway_url = os.getenv('API_GATEWAY_URL', '')
    if gateway_url:
        try:
            payload = json.dumps({
                'origin_lat': origin_lat,
                'origin_lng': origin_lng,
                'destinations': destinations,
            }).encode('utf-8')
            req = urllib.request.Request(
                f"{gateway_url}/distance/matrix",
                data=payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'BRFoodNetwork/1.0'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            pass
    # Fallback: haversine for every destination
    return [
        {'distance_miles': haversine(origin_lat, origin_lng, d['lat'], d['lng']),
         'duration_minutes': None, 'source': 'haversine'}
        for d in destinations
    ]
