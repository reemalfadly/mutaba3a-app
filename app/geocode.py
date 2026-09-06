# -*- coding: utf-8 -*-
"""
البحث عن الأماكن وتحويلها لإحداثيات / Place geocoding
=========================================================

عربي: يستخدم Google Geocoding API لتحويل اسم مكان مكتوب (نص) إلى
      إحداثيات (خط الطول والعرض) وعنوان مكتوب واضح. إذا ما كان مفتاح
      جوجل موجود في app/config.py، الدالة ترجع خطأ واضح بدل ما تسوي
      كراش، وتطلب الشاشة إظهار رسالة "غير مُفعّل" للمستخدم.

English: Uses the Google Geocoding API to turn a typed place name into
         lat/lng coordinates + a formatted address. If no Google Maps
         API key is configured, this safely returns a "not configured"
         error result instead of crashing, and screens should show a
         friendly message to the user.
"""

import json

import requests

from app import config

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

TIMEOUT_SECONDS = 10


class GeocodeResult:
    def __init__(self, ok, formatted_address="", lat=None, lng=None, error=""):
        self.ok = ok
        self.formatted_address = formatted_address
        self.lat = lat
        self.lng = lng
        self.error = error


def is_configured():
    return config.maps_configured()


def geocode_place(query):
    """يبحث عن مكان بالاسم ويرجع أول نتيجة مطابقة.
    Search for a place by name and return the best matching result.

    Returns a GeocodeResult. Never raises -- all failures are captured
    into GeocodeResult.error so the UI can show a friendly message.
    """
    query = (query or "").strip()
    if not query:
        return GeocodeResult(False, error="الرجاء كتابة اسم المكان / Please type a place name")

    if not is_configured():
        return GeocodeResult(
            False,
            error=(
                "ميزة البحث عن الأماكن غير مفعّلة بعد. أضف مفتاح خرائط جوجل "
                "في app/config.py (شوف SETUP.md) / "
                "Places search is not configured yet. Add a Google Maps API "
                "key in app/config.py (see SETUP.md)."
            ),
        )

    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"address": query, "key": config.GOOGLE_MAPS_API_KEY, "language": "ar"},
            timeout=TIMEOUT_SECONDS,
        )
        data = resp.json()
    except requests.RequestException as exc:
        return GeocodeResult(False, error=f"تعذر الاتصال بالإنترنت / Network error: {exc}")
    except (ValueError, json.JSONDecodeError):
        return GeocodeResult(False, error="استجابة غير متوقعة من الخادم / Unexpected server response")

    status = data.get("status")
    if status != "OK":
        friendly = {
            "ZERO_RESULTS": "ما لقينا هذا المكان، جرب اسم آخر / Place not found, try another name",
            "REQUEST_DENIED": "مفتاح خرائط جوجل غير صالح / Invalid Google Maps API key",
            "OVER_QUERY_LIMIT": "تم تجاوز حد الاستخدام اليومي / Daily quota exceeded",
        }.get(status, f"خطأ: {status}")
        return GeocodeResult(False, error=friendly)

    results = data.get("results") or []
    if not results:
        return GeocodeResult(False, error="ما لقينا هذا المكان / Place not found")

    top = results[0]
    location = top.get("geometry", {}).get("location", {})
    return GeocodeResult(
        True,
        formatted_address=top.get("formatted_address", ""),
        lat=location.get("lat"),
        lng=location.get("lng"),
    )
