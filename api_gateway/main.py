"""
API Gateway – centralises external API calls made server-side:
  - Stripe  (payment checkout sessions, webhooks, session retrieval)
  - OpenStreetMap Nominatim  (postcode → lat/lng geocoding)
  - Google Distance Matrix API  (driving miles + ETA between two points)

Note: Google Maps JS is loaded client-side in the browser and does NOT go
through this gateway.  The GOOGLE_MAPS_API_KEY stays in BOTH containers:
  - web:  Django injects it into the producers.html template for the map
  - api:  used here for server-side Distance Matrix calls

The Django web container calls this service via http://api:8001/
so the Stripe secret key is never needed in the web container.
"""

import math
import os
import httpx
import stripe

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="BRFoodNetwork API Gateway", version="1.0.0")

# --------------------------------------------------------------------------- #
# Configuration                                                                 #
# --------------------------------------------------------------------------- #
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

stripe.api_key = STRIPE_SECRET_KEY


def _stripe_ready() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY != "sk_test_placeholder")


# --------------------------------------------------------------------------- #
# Health                                                                        #
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {
        "status": "ok",
        "stripe": "configured" if _stripe_ready() else "placeholder",
        "distance_matrix": "configured" if GOOGLE_MAPS_API_KEY else "haversine_fallback",
    }


# --------------------------------------------------------------------------- #
# Stripe – checkout session                                                     #
# --------------------------------------------------------------------------- #
@app.post("/payments/checkout-session")
async def create_checkout_session(request: Request):
    """
    Create a Stripe Checkout Session.
    Expects a JSON body matching the stripe.checkout.Session.create() kwargs.
    """
    if not _stripe_ready():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    body = await request.json()
    try:
        session = stripe.checkout.Session.create(**body)
        return JSONResponse({"id": session.id, "url": session.url})
    except stripe.StripeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --------------------------------------------------------------------------- #
# Stripe – webhook                                                              #
# --------------------------------------------------------------------------- #
@app.post("/payments/webhook")
async def stripe_webhook(request: Request):
    """
    Forward / validate Stripe webhook events.
    Returns the verified event payload so the web container can act on it.
    """
    if not _stripe_ready():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature")

    return JSONResponse({"type": event["type"], "data": event["data"]})


# --------------------------------------------------------------------------- #
# Stripe – retrieve session                                                     #
# --------------------------------------------------------------------------- #
@app.get("/payments/session/{session_id}")
async def retrieve_session(session_id: str):
    """Retrieve a Stripe Checkout Session by ID."""
    if not _stripe_ready():
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["line_items", "payment_intent"],
        )
        return JSONResponse(dict(session))
    except stripe.StripeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --------------------------------------------------------------------------- #
# OpenStreetMap Nominatim – geocoding                                           #
# (called server-side when a user registers/updates their account postcode)    #
# --------------------------------------------------------------------------- #
@app.get("/geocode")
async def geocode(address: str = "", postal_code: str = ""):
    """
    Convert a UK postcode (or address) to (lat, lng) using OSM Nominatim.
    This mirrors the logic in accounts/geocoding.py so the web container
    can delegate outbound HTTP to the gateway instead of calling OSM directly.
    """
    query = (
        f"{postal_code.strip().upper()}, UK"
        if postal_code
        else f"{address}, UK"
    )

    import urllib.parse

    params = urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "gb"}
    )
    osm_url = f"https://nominatim.openstreetmap.org/search?{params}"
    async with httpx.AsyncClient(
        timeout=5, headers={"User-Agent": "BRFoodNetwork/1.0"}
    ) as client:
        resp = await client.get(osm_url)
    results = resp.json()
    if results:
        return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}

    return {"lat": None, "lng": None}


# --------------------------------------------------------------------------- #
# Google Distance Matrix – single pair                                          #
# --------------------------------------------------------------------------- #
def _haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


@app.get("/distance")
async def driving_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float):
    """
    Driving distance (miles) and duration (minutes) between two points.
    Uses Google Distance Matrix API when a key is configured; falls back
    to straight-line haversine distance with no duration when it is not.
    """
    if GOOGLE_MAPS_API_KEY:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{origin_lat},{origin_lng}",
            "destinations": f"{dest_lat},{dest_lng}",
            "units": "imperial",
            "key": GOOGLE_MAPS_API_KEY,
        }
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, params=params)
        element = resp.json().get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") == "OK":
            return {
                "distance_miles": round(element["distance"]["value"] * 0.000621371, 2),
                "duration_minutes": round(element["duration"]["value"] / 60, 1),
                "source": "google",
            }

    # Fallback: straight-line haversine (no drive time available)
    return {
        "distance_miles": _haversine_miles(origin_lat, origin_lng, dest_lat, dest_lng),
        "duration_minutes": None,
        "source": "haversine",
    }


# --------------------------------------------------------------------------- #
# Google Distance Matrix – batch (one origin → many destinations)              #
# --------------------------------------------------------------------------- #
class _Destination(BaseModel):
    lat: float
    lng: float


class _DistanceMatrixRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destinations: list[_Destination]


@app.post("/distance/matrix")
async def distance_matrix(body: _DistanceMatrixRequest):
    """
    Driving distances and durations from one origin to multiple destinations.
    Returns a list in the same order as the input destinations list.
    Each element: {"distance_miles": float, "duration_minutes": float|null, "source": str}
    """
    if not body.destinations:
        return []

    if GOOGLE_MAPS_API_KEY:
        dest_str = "|".join(f"{d.lat},{d.lng}" for d in body.destinations)
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{body.origin_lat},{body.origin_lng}",
            "destinations": dest_str,
            "units": "imperial",
            "key": GOOGLE_MAPS_API_KEY,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
        elements = resp.json().get("rows", [{}])[0].get("elements", [])
        if len(elements) == len(body.destinations):
            results = []
            for el in elements:
                if el.get("status") == "OK":
                    results.append({
                        "distance_miles": round(el["distance"]["value"] * 0.000621371, 2),
                        "duration_minutes": round(el["duration"]["value"] / 60, 1),
                        "source": "google",
                    })
                else:
                    # Single destination failed – fallback to haversine for that one
                    results.append({
                        "distance_miles": None,
                        "duration_minutes": None,
                        "source": "google_error",
                    })
            return results

    # Fallback: haversine for all destinations
    return [
        {
            "distance_miles": _haversine_miles(body.origin_lat, body.origin_lng, d.lat, d.lng),
            "duration_minutes": None,
            "source": "haversine",
        }
        for d in body.destinations
    ]
