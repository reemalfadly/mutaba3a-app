# -*- coding: utf-8 -*-
"""شاشة الإعدادات / Settings screen.

عربي: تعرض حالة الإعداد (هل مفتاح خرائط جوجل موجود؟ هل فايربيز مُعدّ؟)،
      وتتيح إدخال موقع يدوي (خط طول/عرض) لتجربة مواقيت الصلاة على
      الكمبيوتر بدون GPS، وزر "مزامنة الآن" لتشغيل المزامنة السحابية.

English: Shows configuration status (is the Google Maps key set? is
         Firebase configured?), lets the user enter a manual lat/lng
         for testing prayer times without GPS (e.g. on desktop), and a
         "Sync now" button to trigger cloud sync.
"""

import threading

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.clock import mainthread

from app import config
from app.db import get_db
from app.geocode import is_configured as maps_is_configured
from app.sync_firebase import sync_now, is_configured as firebase_is_configured

KV = """
<SettingsScreen>:
    name: "settings"
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
                    rgba: app.theme_colors["primary_dark"]
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "الإعدادات - Settings"
                color: 1, 1, 1, 1
                font_size: "18sp"
                bold: True

        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: "16dp"
                spacing: "14dp"

                Label:
                    id: maps_status
                    text: ""
                    size_hint_y: None
                    height: "50dp"
                    color: app.theme_colors["text_primary"]
                    text_size: self.width, None
                    halign: "right"

                Label:
                    id: firebase_status
                    text: ""
                    size_hint_y: None
                    height: "50dp"
                    color: app.theme_colors["text_primary"]
                    text_size: self.width, None
                    halign: "right"

                Label:
                    text: "موقع يدوي لتجربة مواقيت الصلاة (بدون GPS):\\nManual location for testing prayer times:"
                    size_hint_y: None
                    height: "50dp"
                    color: app.theme_colors["text_muted"]
                    text_size: self.width, None
                    halign: "right"

                TextInput:
                    id: lat_input
                    hint_text: "خط العرض / Latitude (e.g. 21.4225)"
                    multiline: False
                    size_hint_y: None
                    height: "44dp"

                TextInput:
                    id: lng_input
                    hint_text: "خط الطول / Longitude (e.g. 39.8262)"
                    multiline: False
                    size_hint_y: None
                    height: "44dp"

                Button:
                    text: "حفظ الموقع اليدوي / Save manual location"
                    size_hint_y: None
                    height: "44dp"
                    background_color: app.theme_colors["accent_teal"]
                    on_release: root.save_manual_location()

                Button:
                    text: "مزامنة الآن / Sync now"
                    size_hint_y: None
                    height: "44dp"
                    background_color: app.theme_colors["secondary"]
                    on_release: root.sync_now()

                Label:
                    id: sync_status
                    text: ""
                    size_hint_y: None
                    height: "80dp"
                    color: app.theme_colors["text_muted"]
                    text_size: self.width, None
                    halign: "right"
"""

try:
    Builder.load_string(KV)
except Exception:
    pass


class SettingsScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh_status()

    def refresh_status(self):
        maps_txt = (
            "✅ مفتاح خرائط جوجل موجود / Google Maps key configured"
            if maps_is_configured()
            else "⚠️ مفتاح خرائط جوجل غير موجود - أضفه في app/config.py\n"
                 "Google Maps key not set - add it in app/config.py"
        )
        self.ids.maps_status.text = maps_txt

        fb_txt = (
            "✅ إعدادات فايربيز موجودة / Firebase configured"
            if firebase_is_configured()
            else "⚠️ فايربيز غير معدّ - أضف الإعدادات في app/config.py\n"
                 "Firebase not configured - add settings in app/config.py"
        )
        self.ids.firebase_status.text = fb_txt

        settings = get_db().get_prayer_settings()
        if settings and settings.get("lat") is not None:
            self.ids.lat_input.text = str(settings["lat"])
            self.ids.lng_input.text = str(settings["lng"])

    def save_manual_location(self):
        try:
            lat = float(self.ids.lat_input.text.strip())
            lng = float(self.ids.lng_input.text.strip())
        except ValueError:
            self.ids.sync_status.text = "الرجاء إدخال أرقام صحيحة / Please enter valid numbers"
            return
        get_db().save_prayer_location(lat, lng)
        self.ids.sync_status.text = "تم حفظ الموقع اليدوي / Manual location saved"

    def sync_now(self):
        self.ids.sync_status.text = "جاري المزامنة... / Syncing..."
        threading.Thread(target=self._sync_in_background, daemon=True).start()

    def _sync_in_background(self):
        result = sync_now()
        self._on_sync_result(result)

    @mainthread
    def _on_sync_result(self, result):
        self.ids.sync_status.text = result.message
