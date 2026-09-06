# -*- coding: utf-8 -*-
"""شاشة مواقيت الصلاة / Prayer times screen.

عربي: تعرض مواقيت الصلوات الخمس لليوم بالاعتماد على موقع الجهاز (GPS)،
      مع مفتاح تشغيل/إيقاف تذكير لكل صلاة. الجلب يتم في خيط منفصل حتى
      لا يتجمد التطبيق أثناء انتظار GPS/الإنترنت.

English: Shows today's five prayer times based on device GPS location,
         with a per-prayer reminder on/off toggle. Fetching happens on
         a background thread so the UI doesn't freeze while waiting for
         GPS / network.
"""

import json
import threading

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import mainthread
from kivy.graphics import Color, RoundedRectangle

from app.prayer_times import get_today_timings, PRAYER_NAMES_AR, MAIN_PRAYERS
from app.db import get_db
from app.theme import COLORS

KV = """
<PrayerScreen>:
    name: "prayer"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: app.theme_colors["background"]
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: "12dp", "8dp"
            canvas.before:
                Color:
                    rgba: app.theme_colors["accent_teal"]
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "مواقيت الصلاة - Prayer Times"
                color: 1, 1, 1, 1
                font_size: "18sp"
                bold: True

        BoxLayout:
            size_hint_y: None
            height: "44dp"
            padding: "8dp", "4dp"
            Button:
                text: "تحديث / Refresh"
                background_color: app.theme_colors["primary"]
                on_release: root.refresh()

        Label:
            id: status_label
            text: ""
            size_hint_y: None
            height: "30dp"
            color: app.theme_colors["text_muted"]

        ScrollView:
            BoxLayout:
                id: prayer_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: "10dp"
                spacing: "10dp"
"""

try:
    Builder.load_string(KV)
except Exception:
    pass


class PrayerScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.ids.status_label.text = "جاري تحديد موقعك وجلب المواقيت... / Locating & fetching..."
        self.ids.prayer_list.clear_widgets()
        threading.Thread(target=self._fetch_in_background, daemon=True).start()

    def _fetch_in_background(self):
        result = get_today_timings()
        self._on_result(result)

    @mainthread
    def _on_result(self, result):
        container = self.ids.prayer_list
        container.clear_widgets()
        if not result.ok:
            self.ids.status_label.text = result.error
            return

        source_note = "📍 حسب موقعك الحالي (GPS)" if result.source == "gps" else "📍 حسب موقع محفوظ يدوياً (تجربة)"
        self.ids.status_label.text = source_note

        db = get_db()
        settings = db.get_prayer_settings() or {}
        reminders = {}
        try:
            reminders = json.loads(settings.get("reminders_json") or "{}")
        except (ValueError, TypeError):
            reminders = {}

        for prayer in MAIN_PRAYERS:
            container.add_widget(self._build_row(prayer, result.timings.get(prayer, "--:--"), reminders))

    def _build_row(self, prayer_key, time_str, reminders):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="56dp",
                         padding=("12dp", "6dp"), spacing="10dp")
        with row.canvas.before:
            Color(*COLORS["surface"])
            rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[14])
        def _update_rect(instance, _value, rect=rect):
            rect.pos = instance.pos
            rect.size = instance.size
        row.bind(pos=_update_rect, size=_update_rect)

        row.add_widget(Label(text=PRAYER_NAMES_AR.get(prayer_key, prayer_key),
                              color=COLORS["text_primary"], font_size="16sp", bold=True))
        row.add_widget(Label(text=time_str, color=COLORS["secondary"], font_size="16sp"))

        enabled = reminders.get(prayer_key, True)
        toggle = Button(
            text=("🔔 تذكير: مفعّل" if enabled else "🔕 تذكير: متوقف"),
            size_hint_x=None, width="150dp",
            background_color=(COLORS["done"] if enabled else COLORS["text_muted"]),
        )

        def on_toggle(_btn, prayer_key=prayer_key):
            db = get_db()
            settings = db.get_prayer_settings() or {}
            try:
                current = json.loads(settings.get("reminders_json") or "{}")
            except (ValueError, TypeError):
                current = {}
            current[prayer_key] = not current.get(prayer_key, True)
            db.save_prayer_reminders(json.dumps(current))
            self.refresh()

        toggle.bind(on_release=on_toggle)
        row.add_widget(toggle)
        return row
