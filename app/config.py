# -*- coding: utf-8 -*-
"""
إعدادات التطبيق / App configuration
=====================================

عربي:
    هذا هو المكان الوحيد اللي لازم تحط فيه المفاتيح (API keys) الخاصة بك.
    التطبيق يشتغل بدون أي مشكلة حتى لو تركت هذي القيم فاضية -- بس بعض
    الميزات (البحث عن الأماكن، والمزامنة السحابية) ما راح تشتغل وبيظهر
    لك رسالة "غير مُفعّل" بدل ما يصير كراش (توقف مفاجئ) للتطبيق.

    شوف ملف SETUP.md للحصول على شرح كامل خطوة بخطوة بالعربي عن طريقة
    الحصول على كل مفتاح ومن وين تجيبه.

English:
    This is the single place you need to paste your API keys.
    The app works completely fine even if you leave these blank --
    only the "Places search" and "Cloud sync" features will be disabled
    and show a friendly "not configured" message instead of crashing.

    See SETUP.md for full Arabic-first step-by-step instructions on how
    to obtain each key.

ملاحظة أمان / Security note:
    لا ترفع هذا الملف بمفاتيح حقيقية إلى مستودع عام (public repo).
    Do not commit this file with real keys to a public repository.
    You can also set these as environment variables with the same
    names instead of editing this file directly (env vars win if set).
"""

import os


def _env_or(default, *names):
    """يرجع أول متغير بيئة موجود، وإلا يرجع القيمة الافتراضية.
    Return the first set environment variable, else the default value."""
    for name in names:
        val = os.environ.get(name)
        if val:
            return val
    return default


# -----------------------------------------------------------------------
# مفتاح خرائط جوجل (Google Maps / Places / Geocoding API key)
# -----------------------------------------------------------------------
# عربي: هذا المفتاح يُستخدم لتحويل اسم مكان كتبته (مثلاً "مسجد النور")
#       إلى إحداثيات (خط الطول والعرض) وعنوان مكتوب واضح.
#       احصل عليه من: https://console.cloud.google.com/
#       فعّل خدمتي: "Geocoding API" و "Places API"
#       التفاصيل الكاملة موجودة في SETUP.md
#
# English: Used to turn a typed place name (e.g. "Al Noor Mosque") into
#          coordinates (lat/lng) + a formatted address.
#          Get it from: https://console.cloud.google.com/
#          Enable: "Geocoding API" and "Places API"
#          Full details in SETUP.md
GOOGLE_MAPS_API_KEY = _env_or("", "MUTABA3A_GOOGLE_MAPS_API_KEY", "GOOGLE_MAPS_API_KEY")

# -----------------------------------------------------------------------
# إعدادات فايربيز (Firebase) للمزامنة السحابية / Cloud sync
# -----------------------------------------------------------------------
# عربي: هذي المفاتيح تُستخدم لحفظ نسخة من بياناتك على الإنترنت (Firestore)
#       حتى لو غيّرت جوالك أو حذفت التطبيق تقدر تسترجعها.
#       أنشئ مشروع مجاني من: https://console.firebase.google.com/
#       التفاصيل الكاملة (خطوة بخطوة) موجودة في SETUP.md
#
# English: Used to back up your data online (Firestore) so you can
#          restore it on a new phone or after reinstalling the app.
#          Create a free project at: https://console.firebase.google.com/
#          Full step-by-step details in SETUP.md
FIREBASE_WEB_API_KEY = _env_or("", "MUTABA3A_FIREBASE_WEB_API_KEY", "FIREBASE_WEB_API_KEY")

# عربي: معرّف مشروع فايربيز (تلقاه في إعدادات المشروع في Firebase Console)
# English: Your Firebase project ID (found in Firebase Console -> Project settings)
FIREBASE_PROJECT_ID = _env_or("", "MUTABA3A_FIREBASE_PROJECT_ID", "FIREBASE_PROJECT_ID")

# عربي: طريقة تسجيل الدخول -- "anonymous" أبسط وما تحتاج بريد إلكتروني،
#       أو "password" لتسجيل دخول بالبريد وكلمة المرور.
# English: Auth mode -- "anonymous" is simplest (no email needed), or
#          "password" for email/password sign-in.
FIREBASE_AUTH_MODE = _env_or("anonymous", "MUTABA3A_FIREBASE_AUTH_MODE", "FIREBASE_AUTH_MODE")

# عربي: البريد الإلكتروني وكلمة المرور (تُستخدم فقط إذا AUTH_MODE = "password")
# English: Email/password (only used if AUTH_MODE == "password")
FIREBASE_USER_EMAIL = _env_or("", "MUTABA3A_FIREBASE_USER_EMAIL", "FIREBASE_USER_EMAIL")
FIREBASE_USER_PASSWORD = _env_or("", "MUTABA3A_FIREBASE_USER_PASSWORD", "FIREBASE_USER_PASSWORD")


def maps_configured():
    """هل مفتاح خرائط جوجل موجود؟ / Is the Google Maps key set?"""
    return bool(GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY.strip())


def firebase_configured():
    """هل إعدادات فايربيز موجودة؟ / Is Firebase configured?"""
    return bool(
        FIREBASE_WEB_API_KEY
        and FIREBASE_WEB_API_KEY.strip()
        and FIREBASE_PROJECT_ID
        and FIREBASE_PROJECT_ID.strip()
    )


# -----------------------------------------------------------------------
# إعدادات مواقيت الصلاة (Aladhan API) -- لا تحتاج مفتاح إطلاقاً
# Prayer times (Aladhan API) -- no API key needed at all
# -----------------------------------------------------------------------
# عربي: رقم طريقة الحساب (method) -- 4 = أم القرى بمكة المكرمة، وهي مناسبة
#       لمعظم المستخدمين في الخليج. غيّرها إذا تحب طريقة حساب مختلفة.
#       القائمة الكاملة: https://aladhan.com/calculation-methods
# English: Calculation method number -- 4 = Umm al-Qura (Makkah), suitable
#          for most Gulf users. Change if you prefer a different method.
#          Full list: https://aladhan.com/calculation-methods
PRAYER_CALCULATION_METHOD = int(_env_or("4", "MUTABA3A_PRAYER_METHOD", "PRAYER_METHOD"))

ALADHAN_BASE_URL = "https://api.aladhan.com/v1/timings"

# عربي: عنوان قاعدة بيانات فايرستور (لا تحتاج تعديله عادة)
# English: Firestore REST base URL (usually no need to change this)
FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1"
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"

APP_NAME_AR = "متابعة"
APP_NAME_EN = "Mutaba3a"
