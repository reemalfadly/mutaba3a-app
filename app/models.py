# -*- coding: utf-8 -*-
"""نماذج البيانات البسيطة / Simple data models used across the app."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    notes: str = ""
    done: bool = False
    due_date: str = ""          # "YYYY-MM-DD" or "" if none
    due_time: str = ""          # "HH:MM" or "" if none
    created_at: str = ""        # ISO timestamp
    completed_at: str = ""      # ISO timestamp or ""
    postponed_count: int = 0
    updated_at: str = ""
    deleted: bool = False
    remote_id: str = ""         # Firestore document id once synced


@dataclass
class TaskHistoryEntry:
    id: Optional[int] = None
    task_id: int = 0
    event: str = ""             # created / completed / uncompleted / postponed / deleted
    from_value: str = ""
    to_value: str = ""
    at: str = ""                # ISO timestamp


@dataclass
class Place:
    id: Optional[int] = None
    name: str = ""
    formatted_address: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    created_at: str = ""


@dataclass
class Appointment:
    id: Optional[int] = None
    title: str = ""
    notes: str = ""
    date: str = ""               # "YYYY-MM-DD"
    time: str = ""                # "HH:MM"
    place_id: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
    deleted: bool = False
    remote_id: str = ""


@dataclass
class PrayerSettings:
    id: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    last_updated: str = ""
    reminders: dict = field(default_factory=lambda: {
        "Fajr": True, "Dhuhr": True, "Asr": True, "Maghrib": True, "Isha": True,
    })
