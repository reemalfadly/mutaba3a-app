# -*- coding: utf-8 -*-
"""
قاعدة البيانات المحلية (SQLite) / Local SQLite database
==========================================================

عربي: كل بيانات التطبيق (المهام، المواعيد، الأماكن، إعدادات الصلاة)
      تُحفظ محلياً في ملف SQLite على الجهاز، فالتطبيق يشتغل بالكامل
      حتى بدون إنترنت. المزامنة السحابية (إن وُجدت) تحدث لاحقاً فوق
      هذي البيانات ولا تحل محلها.

English: All app data (tasks, appointments, places, prayer settings)
         is stored locally in a SQLite file on the device, so the app
         works fully offline. Cloud sync (if configured) happens on
         top of this data later, it does not replace it.
"""

import os
import sqlite3
import threading
from datetime import datetime

try:
    from kivy.app import App
except Exception:  # pragma: no cover - kivy may not be importable in some test contexts
    App = None


def _default_db_path():
    """يحدد أفضل مسار لملف قاعدة البيانات حسب المنصة.
    Determine the best database file path for the current platform."""
    try:
        if App is not None and App.get_running_app() is not None:
            user_dir = App.get_running_app().user_data_dir
            os.makedirs(user_dir, exist_ok=True)
            return os.path.join(user_dir, "mutaba3a.db")
    except Exception:
        pass
    # fallback: local folder next to the project (desktop dev / tests)
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".data")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "mutaba3a.db")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


class Database:
    """طبقة وصول بسيطة لقاعدة البيانات، آمنة لخيط واحد مع قفل.
    A simple data-access layer, thread-safe via a lock."""

    def __init__(self, path=None):
        self.path = path or _default_db_path()
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _init_schema(self):
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    done INTEGER DEFAULT 0,
                    due_date TEXT DEFAULT '',
                    due_time TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    completed_at TEXT DEFAULT '',
                    postponed_count INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    deleted INTEGER DEFAULT 0,
                    remote_id TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    event TEXT NOT NULL,
                    from_value TEXT DEFAULT '',
                    to_value TEXT DEFAULT '',
                    at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    formatted_address TEXT DEFAULT '',
                    lat REAL,
                    lng REAL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '',
                    place_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    deleted INTEGER DEFAULT 0,
                    remote_id TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS prayer_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    lat REAL,
                    lng REAL,
                    last_updated TEXT DEFAULT '',
                    reminders_json TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS sync_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    def add_task(self, title, notes="", due_date="", due_time=""):
        ts = now_iso()
        with self._lock, self._conn:
            cur = self._conn.execute(
                """INSERT INTO tasks (title, notes, done, due_date, due_time,
                   created_at, completed_at, postponed_count, updated_at, deleted)
                   VALUES (?, ?, 0, ?, ?, ?, '', 0, ?, 0)""",
                (title, notes, due_date, due_time, ts, ts),
            )
            task_id = cur.lastrowid
            self._add_history(task_id, "created", "", title)
            return task_id

    def _add_history(self, task_id, event, from_value="", to_value=""):
        self._conn.execute(
            "INSERT INTO task_history (task_id, event, from_value, to_value, at) VALUES (?,?,?,?,?)",
            (task_id, event, str(from_value), str(to_value), now_iso()),
        )

    def list_tasks(self, include_deleted=False):
        q = "SELECT * FROM tasks"
        if not include_deleted:
            q += " WHERE deleted = 0"
        q += " ORDER BY done ASC, due_date ASC, due_time ASC, id DESC"
        with self._lock:
            rows = self._conn.execute(q).fetchall()
        return [dict(r) for r in rows]

    def get_task(self, task_id):
        with self._lock:
            row = self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def set_task_done(self, task_id, done):
        ts = now_iso()
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE tasks SET done=?, completed_at=?, updated_at=? WHERE id=?",
                (1 if done else 0, ts if done else "", ts, task_id),
            )
            self._add_history(task_id, "completed" if done else "uncompleted")

    def postpone_task(self, task_id, new_date, new_time=""):
        task = self.get_task(task_id)
        if not task:
            return
        old = f"{task.get('due_date','')} {task.get('due_time','')}".strip()
        new = f"{new_date} {new_time}".strip()
        ts = now_iso()
        with self._lock, self._conn:
            self._conn.execute(
                """UPDATE tasks SET due_date=?, due_time=?, postponed_count=postponed_count+1,
                   updated_at=? WHERE id=?""",
                (new_date, new_time, ts, task_id),
            )
            self._add_history(task_id, "postponed", old, new)

    def delete_task(self, task_id):
        ts = now_iso()
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE tasks SET deleted=1, updated_at=? WHERE id=?", (ts, task_id)
            )
            self._add_history(task_id, "deleted")

    def task_history(self, task_id):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM task_history WHERE task_id=? ORDER BY at DESC", (task_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Places
    # ------------------------------------------------------------------
    def add_place(self, name, formatted_address="", lat=None, lng=None):
        ts = now_iso()
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO places (name, formatted_address, lat, lng, created_at) VALUES (?,?,?,?,?)",
                (name, formatted_address, lat, lng, ts),
            )
            return cur.lastrowid

    def get_place(self, place_id):
        with self._lock:
            row = self._conn.execute("SELECT * FROM places WHERE id=?", (place_id,)).fetchone()
        return dict(row) if row else None

    def list_places(self):
        with self._lock:
            rows = self._conn.execute("SELECT * FROM places ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------
    def add_appointment(self, title, date, time="", notes="", place_id=None):
        ts = now_iso()
        with self._lock, self._conn:
            cur = self._conn.execute(
                """INSERT INTO appointments (title, notes, date, time, place_id,
                   created_at, updated_at, deleted) VALUES (?,?,?,?,?,?,?,0)""",
                (title, notes, date, time, place_id, ts, ts),
            )
            return cur.lastrowid

    def update_appointment(self, appt_id, **fields):
        if not fields:
            return
        fields["updated_at"] = now_iso()
        cols = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [appt_id]
        with self._lock, self._conn:
            self._conn.execute(f"UPDATE appointments SET {cols} WHERE id=?", vals)

    def delete_appointment(self, appt_id):
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE appointments SET deleted=1, updated_at=? WHERE id=?",
                (now_iso(), appt_id),
            )

    def list_appointments(self, include_deleted=False):
        q = "SELECT * FROM appointments"
        if not include_deleted:
            q += " WHERE deleted = 0"
        q += " ORDER BY date ASC, time ASC"
        with self._lock:
            rows = self._conn.execute(q).fetchall()
        return [dict(r) for r in rows]

    def get_appointment(self, appt_id):
        with self._lock:
            row = self._conn.execute("SELECT * FROM appointments WHERE id=?", (appt_id,)).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Prayer settings
    # ------------------------------------------------------------------
    def get_prayer_settings(self):
        with self._lock:
            row = self._conn.execute("SELECT * FROM prayer_settings WHERE id=1").fetchone()
        return dict(row) if row else None

    def save_prayer_location(self, lat, lng):
        ts = now_iso()
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO prayer_settings (id, lat, lng, last_updated, reminders_json)
                   VALUES (1, ?, ?, ?, COALESCE((SELECT reminders_json FROM prayer_settings WHERE id=1), ''))
                   ON CONFLICT(id) DO UPDATE SET lat=excluded.lat, lng=excluded.lng, last_updated=excluded.last_updated""",
                (lat, lng, ts),
            )

    def save_prayer_reminders(self, reminders_json):
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO prayer_settings (id, reminders_json) VALUES (1, ?)
                   ON CONFLICT(id) DO UPDATE SET reminders_json=excluded.reminders_json""",
                (reminders_json,),
            )

    # ------------------------------------------------------------------
    # Sync metadata (for Firestore sync bookkeeping)
    # ------------------------------------------------------------------
    def get_meta(self, key, default=None):
        with self._lock:
            row = self._conn.execute("SELECT value FROM sync_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key, value):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO sync_meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def set_task_remote_id(self, task_id, remote_id):
        with self._lock, self._conn:
            self._conn.execute("UPDATE tasks SET remote_id=? WHERE id=?", (remote_id, task_id))

    def set_appointment_remote_id(self, appt_id, remote_id):
        with self._lock, self._conn:
            self._conn.execute("UPDATE appointments SET remote_id=? WHERE id=?", (remote_id, appt_id))

    def close(self):
        with self._lock:
            self._conn.close()


_instance = None
_instance_lock = threading.Lock()


def get_db():
    """يرجع نسخة واحدة مشتركة من قاعدة البيانات (singleton).
    Return a shared singleton Database instance."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = Database()
        return _instance
