# -*- coding: utf-8 -*-
"""
المزامنة السحابية عبر Firestore REST API / Cloud sync via Firestore REST
============================================================================

عربي: هذا الملف مسؤول عن رفع/تنزيل بياناتك (المهام والمواعيد) من وإلى
      Firebase Firestore، باستخدام واجهة REST مباشرة عبر مكتبة requests
      (بدون تثبيت مكتبات Firebase الثقيلة اللي تعقّد بناء تطبيق Kivy).

      مهم جداً: التطبيق يشتغل بالكامل بدون إنترنت أو بدون إعداد فايربيز.
      إذا ما كانت الإعدادات موجودة في app/config.py، كل دالة هنا ترجع
      "غير مفعّل" بهدوء بدون أي كراش، والبيانات المحلية (SQLite) تبقى
      هي المصدر الرئيسي دائماً.

English: Responsible for pushing/pulling your data (tasks & appointments)
         to/from Firebase Firestore using the REST API directly via
         `requests` (avoiding heavy Firebase SDKs that complicate a
         Kivy/Android build).

         Important: the app works fully offline / without Firebase
         configured. If config.py is missing the required values, every
         function here safely no-ops and reports "not configured" --
         local SQLite always remains the source of truth.
"""

import json
import time

import requests

from app import config
from app.db import get_db

TIMEOUT_SECONDS = 12


class SyncResult:
    def __init__(self, ok, message="", pushed=0, pulled=0):
        self.ok = ok
        self.message = message
        self.pushed = pushed
        self.pulled = pulled


def is_configured():
    return config.firebase_configured()


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------
def _sign_in_anonymous():
    url = f"{config.FIREBASE_AUTH_BASE_URL}/accounts:signUp"
    resp = requests.post(
        url, params={"key": config.FIREBASE_WEB_API_KEY}, json={"returnSecureToken": True},
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def _sign_in_password():
    url = f"{config.FIREBASE_AUTH_BASE_URL}/accounts:signInWithPassword"
    payload = {
        "email": config.FIREBASE_USER_EMAIL,
        "password": config.FIREBASE_USER_PASSWORD,
        "returnSecureToken": True,
    }
    resp = requests.post(url, params={"key": config.FIREBASE_WEB_API_KEY}, json=payload, timeout=TIMEOUT_SECONDS)
    if resp.status_code == 400:
        # try signUp in case the account doesn't exist yet
        url_signup = f"{config.FIREBASE_AUTH_BASE_URL}/accounts:signUp"
        resp = requests.post(url_signup, params={"key": config.FIREBASE_WEB_API_KEY}, json=payload, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def _get_auth():
    """يرجع (id_token, user_id) ويستخدم رمز مخزّن إذا ما زال صالح.
    Return (id_token, user_id), reusing a cached token while still valid."""
    db = get_db()
    cached_token = db.get_meta("firebase_id_token")
    cached_uid = db.get_meta("firebase_user_id")
    cached_exp = db.get_meta("firebase_token_expiry")
    if cached_token and cached_uid and cached_exp:
        try:
            if time.time() < float(cached_exp) - 60:
                return cached_token, cached_uid
        except ValueError:
            pass

    mode = (config.FIREBASE_AUTH_MODE or "anonymous").lower()
    if mode == "password" and config.FIREBASE_USER_EMAIL and config.FIREBASE_USER_PASSWORD:
        data = _sign_in_password()
    else:
        data = _sign_in_anonymous()

    id_token = data.get("idToken")
    uid = data.get("localId")
    expires_in = float(data.get("expiresIn", 3600))
    db.set_meta("firebase_id_token", id_token)
    db.set_meta("firebase_user_id", uid)
    db.set_meta("firebase_token_expiry", str(time.time() + expires_in))
    return id_token, uid


# ---------------------------------------------------------------------
# Firestore REST helpers
# ---------------------------------------------------------------------
def _doc_url(uid, collection, doc_id=None):
    base = f"{config.FIRESTORE_BASE_URL}/projects/{config.FIREBASE_PROJECT_ID}/databases/(default)/documents"
    path = f"{base}/users/{uid}/{collection}"
    if doc_id:
        path += f"/{doc_id}"
    return path


def _to_firestore_fields(d):
    """يحوّل قاموس بايثون بسيط إلى صيغة حقول فايرستور.
    Convert a flat Python dict into Firestore's `fields` JSON structure."""
    fields = {}
    for key, value in d.items():
        if value is None:
            fields[key] = {"nullValue": None}
        elif isinstance(value, bool):
            fields[key] = {"booleanValue": value}
        elif isinstance(value, int):
            fields[key] = {"integerValue": str(value)}
        elif isinstance(value, float):
            fields[key] = {"doubleValue": value}
        else:
            fields[key] = {"stringValue": str(value)}
    return {"fields": fields}


def _from_firestore_fields(doc):
    """يحوّل مستند فايرستور رجوعاً إلى قاموس بايثون بسيط.
    Convert a Firestore document back into a flat Python dict."""
    out = {}
    for key, value in doc.get("fields", {}).items():
        if "integerValue" in value:
            out[key] = int(value["integerValue"])
        elif "doubleValue" in value:
            out[key] = float(value["doubleValue"])
        elif "booleanValue" in value:
            out[key] = bool(value["booleanValue"])
        elif "nullValue" in value:
            out[key] = None
        else:
            out[key] = value.get("stringValue", "")
    doc_name = doc.get("name", "")
    out["_remote_id"] = doc_name.rsplit("/", 1)[-1] if doc_name else ""
    return out


def _headers(id_token):
    return {"Authorization": f"Bearer {id_token}", "Content-Type": "application/json"}


def _push_collection(id_token, uid, collection, rows, id_field, remote_setter):
    pushed = 0
    for row in rows:
        row_id = row.get(id_field)
        remote_id = row.get("remote_id") or f"local-{collection}-{row_id}"
        body = {k: v for k, v in row.items() if k not in ("remote_id",)}
        url = _doc_url(uid, collection, remote_id)
        resp = requests.patch(
            url,
            params={"key": config.FIREBASE_WEB_API_KEY},
            headers=_headers(id_token),
            json=_to_firestore_fields(body),
            timeout=TIMEOUT_SECONDS,
        )
        if resp.status_code in (200, 201):
            pushed += 1
            if not row.get("remote_id"):
                remote_setter(row_id, remote_id)
    return pushed


def _pull_collection(id_token, uid, collection):
    url = _doc_url(uid, collection)
    resp = requests.get(
        url, params={"key": config.FIREBASE_WEB_API_KEY}, headers=_headers(id_token), timeout=TIMEOUT_SECONDS
    )
    if resp.status_code != 200:
        return []
    data = resp.json()
    docs = data.get("documents", [])
    return [_from_firestore_fields(d) for d in docs]


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def sync_now():
    """يزامن المهام والمواعيد مع Firestore إذا كانت الإعدادات موجودة والاتصال متاح.
    Sync tasks & appointments with Firestore if configured and reachable.
    Always safe to call -- returns SyncResult with ok=False and a
    friendly message instead of raising when unconfigured/offline.
    """
    if not is_configured():
        return SyncResult(
            False,
            message=(
                "المزامنة السحابية غير مفعّلة بعد. أضف إعدادات فايربيز في "
                "app/config.py (شوف SETUP.md) / Cloud sync is not configured "
                "yet. Add Firebase settings in app/config.py (see SETUP.md)."
            ),
        )

    db = get_db()
    try:
        id_token, uid = _get_auth()
    except requests.RequestException as exc:
        return SyncResult(False, message=f"تعذر الاتصال بالإنترنت / Network error: {exc}")
    except Exception as exc:  # invalid config, bad response, etc.
        return SyncResult(False, message=f"تعذر تسجيل الدخول للمزامنة / Sign-in failed: {exc}")

    pushed_total = 0
    try:
        tasks = [t for t in db.list_tasks(include_deleted=True)]
        pushed_total += _push_collection(
            id_token, uid, "tasks", tasks, "id", db.set_task_remote_id
        )

        appts = [a for a in db.list_appointments(include_deleted=True)]
        pushed_total += _push_collection(
            id_token, uid, "appointments", appts, "id", db.set_appointment_remote_id
        )
    except requests.RequestException as exc:
        return SyncResult(False, message=f"انقطع الاتصال أثناء الرفع / Network error while pushing: {exc}")

    pulled_total = 0
    try:
        remote_tasks = _pull_collection(id_token, uid, "tasks")
        remote_appts = _pull_collection(id_token, uid, "appointments")
        pulled_total = _merge_remote(db, remote_tasks, remote_appts)
    except requests.RequestException as exc:
        return SyncResult(False, message=f"انقطع الاتصال أثناء التنزيل / Network error while pulling: {exc}")

    db.set_meta("last_sync_at", str(time.time()))
    return SyncResult(
        True,
        message=f"تمت المزامنة بنجاح / Sync complete ({pushed_total} pushed, {pulled_total} pulled)",
        pushed=pushed_total,
        pulled=pulled_total,
    )


def _merge_remote(db, remote_tasks, remote_appts):
    """يدمج نسخة بسيطة: أي مستند بعيد ما له مطابقة محلية (remote_id) يُضاف محلياً.
    Simple last-write-wins-ish merge: any remote doc without a matching
    local remote_id gets inserted locally. This keeps things simple and
    resilient rather than implementing full conflict resolution.
    """
    merged = 0
    local_tasks_remote_ids = {t.get("remote_id") for t in db.list_tasks(include_deleted=True) if t.get("remote_id")}
    for rt in remote_tasks:
        rid = rt.get("_remote_id")
        if rid and rid not in local_tasks_remote_ids:
            new_id = db.add_task(
                rt.get("title", ""), rt.get("notes", ""), rt.get("due_date", ""), rt.get("due_time", "")
            )
            db.set_task_remote_id(new_id, rid)
            if rt.get("done"):
                db.set_task_done(new_id, True)
            merged += 1

    local_appt_remote_ids = {
        a.get("remote_id") for a in db.list_appointments(include_deleted=True) if a.get("remote_id")
    }
    for ra in remote_appts:
        rid = ra.get("_remote_id")
        if rid and rid not in local_appt_remote_ids:
            new_id = db.add_appointment(
                ra.get("title", ""), ra.get("date", ""), ra.get("time", ""), ra.get("notes", "")
            )
            db.set_appointment_remote_id(new_id, rid)
            merged += 1

    return merged
