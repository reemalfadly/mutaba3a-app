# -*- coding: utf-8 -*-
"""
مواقيت الصلاة / Prayer times
================================

عربي: يجلب مواقيت الصلاة الخمسة لليوم بالاعتماد على موقع الجهاز (GPS)
      باستخدام خدمة Aladhan المجانية (بدون أي مفتاح API). يحاول أولاً
      قراءة الموقع عبر plyer.gps (يشتغل على أندرويد)، وإذا ما كان
      متوفر (مثلاً أثناء التجربة على الكمبيوتر) يرجع للموقع المحفوظ
      يدوياً في إعدادات التطبيق.

English: Fetches today's five prayer times based on the device's GPS
         location using the free Aladhan API (no API key required).
         It first tries to read location via plyer.gps (works on
         Android), and falls back to a manually-entered location saved
         in app settings (useful for desktop testing).
"""

import json
import threading
import time

import requests

from app import config
from app.db import get_db

PRAYER_NAMES_AR = {
    "Fajr": "الفجر",
    "Sunrise": "الشروق",
    "Dhuhr": "الظهر",
    "Asr": "العصر",
    "Maghrib": "المغرب",
    "Isha": "العشاء",
}

MAIN_PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

TIMEOUT_SECONDS = 10


class PrayerResult:
    def __init__(self, ok, timings=None, error="", lat=None, lng=None, source=""):
        self.ok = ok
        self.timings = timings or {}
        self.error = error
        self.lat = lat
        self.lng = lng
        self.source = source  # "gps" or "manual"


def fetch_timings_for_location(lat, lng):
    """يستدعي واجهة Aladhan لجلب مواقيت اليوم لإحداثيات معيّنة.
    Call the Aladhan API to get today's timings for a given lat/lng.
    Never raises -- errors are captured in PrayerResult.error."""
    try:
        resp = requests.get(
            config.ALADHAN_BASE_URL,
            params={
                "latitude": lat,
                "longitude": lng,
                "method": config.PRAYER_CALCULATION_METHOD,
            },
            timeout=TIMEOUT_SECONDS,
        )
        data = resp.json()
    except requests.RequestException as exc:
        return PrayerResult(False, error=f"تعذر الاتصال بخدمة مواقيت الصلاة / Network error: {exc}")
    except (ValueError, json.JSONDecodeError):
        return PrayerResult(False, error="استجابة غير متوقعة من خدمة مواقيت الصلاة / Unexpected response")

    if data.get("code") != 200:
        return PrayerResult(False, error="تعذر جلب مواقيت الصلاة الآن / Could not fetch prayer times right now")

    timings_raw = data.get("data", {}).get("timings", {})
    timings = {name: timings_raw.get(name, "--:--") for name in MAIN_PRAYERS}
    return PrayerResult(True, timings=timings, lat=lat, lng=lng, source="api")


def get_current_location(timeout=8):
    """يحاول قراءة موقع GPS الحالي عبر plyer، وإلا يرجع آخر موقع محفوظ يدوياً.
    Try to read the current GPS location via plyer; otherwise fall back
    to the last manually-saved location. Returns (lat, lng, source) or
    (None, None, "") if nothing is available.
    """
    lat_lng = {"lat": None, "lng": None}
    got_fix = threading.Event()

    def on_location(**kwargs):
        lat_lng["lat"] = kwargs.get("lat")
        lat_lng["lng"] = kwargs.get("lon", kwargs.get("lng"))
        got_fix.set()

    def on_status(stype, status):
        pass

    try:
        from plyer import gps  # noqa: WPS433 -- optional/platform dependent import

        gps.configure(on_location=on_location, on_status=on_status)
        gps.start(minTime=1000, minDistance=0)
        got_fix.wait(timeout)
        try:
            gps.stop()
        except Exception:
            pass
        if lat_lng["lat"] is not None and lat_lng["lng"] is not None:
            return lat_lng["lat"], lat_lng["lng"], "gps"
    except NotImplementedError:
        pass  # GPS not supported on this platform (e.g. desktop)
    except Exception:
        pass  # any other plyer/platform failure -- fall back gracefully

    # Fallback: manually saved location (for desktop testing or if GPS fails)
    db = get_db()
    settings = db.get_prayer_settings()
    if settings and settings.get("lat") is not None and settings.get("lng") is not None:
        return settings["lat"], settings["lng"], "manual"

    return None, None, ""


def get_today_timings():
    """الدالة الرئيسية: تجلب مواقيت اليوم بالاعتماد على GPS أو الموقع اليدوي.
    Main entry point: fetch today's timings using GPS or manual fallback."""
    lat, lng, source = get_current_location()
    if lat is None or lng is None:
        return PrayerResult(
            False,
            error=(
                "ما قدرنا نحدد موقعك. فعّل خدمة الموقع (GPS) أو أدخل الموقع "
                "يدوياً في الإعدادات / Could not determine your location. "
                "Enable GPS or enter a location manually in Settings."
            ),
        )
    result = fetch_timings_for_location(lat, lng)
    result.source = source
    if result.ok:
        db = get_db()
        db.save_prayer_location(lat, lng)
    return result
