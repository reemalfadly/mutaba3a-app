# -*- coding: utf-8 -*-
"""
تطبيق متابعة (Mutaba3a) - نقطة البداية / App entry point
=============================================================

عربي: تطبيق شخصي لمتابعة المهام والمواعيد ومواقيت الصلاة، مبني بلغة
      بايثون باستخدام Kivy. يعمل بالكامل دون إنترنت (SQLite محلي)،
      ويزامن البيانات اختيارياً مع Firebase إذا تم إعداده.

English: A personal task/appointment/prayer-times tracking app built
         in Python with Kivy. Works fully offline (local SQLite), and
         optionally syncs to Firebase once configured.

ملاحظة تقنية / Technical note:
    اخترنا استخدام Kivy العادي (بدون KivyMD) لتقليل مخاطر فشل بناء
    APK على GitHub Actions، لأن KivyMD تضيف تعقيد إضافي بالنسخ
    والاعتماديات على أندرويد. نفّذنا مظهر ملوّن ومبهج يدوياً عبر
    app/theme.py بدلاً من ذلك.

    We chose plain Kivy (without KivyMD) to reduce the risk of the
    Android APK build failing in CI, since KivyMD adds extra
    version/dependency complexity on Android. We implemented a bright,
    cheerful custom look by hand via app/theme.py instead.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle

from app.theme import COLORS
from app.db import get_db
from app.screens.todo_screen import TodoScreen
from app.screens.calendar_screen import CalendarScreen
from app.screens.prayer_screen import PrayerScreen
from app.screens.settings_screen import SettingsScreen

ROOT_KV = """
<RootLayout>:
    orientation: "vertical"

    ScreenManager:
        id: screen_manager

    BoxLayout:
        id: nav_bar
        size_hint_y: None
        height: "56dp"
"""

try:
    Builder.load_string(ROOT_KV)
except Exception:
    pass


class RootLayout(BoxLayout):
    pass


class Mutaba3aApp(App):
    """التطبيق الرئيسي / Main application class."""

    title = "متابعة - Mutaba3a"

    # عربي: يوفر الألوان لجميع ملفات kv عبر app.theme_colors
    # English: Exposes colors to all kv files via app.theme_colors
    theme_colors = COLORS

    def build(self):
        # تهيئة قاعدة البيانات مبكراً / Initialize the DB early
        get_db()

        root = RootLayout()
        sm = root.ids.screen_manager
        sm.transition = FadeTransition(duration=0.15)
        sm.add_widget(TodoScreen(name="todo"))
        sm.add_widget(CalendarScreen(name="calendar"))
        sm.add_widget(PrayerScreen(name="prayer"))
        sm.add_widget(SettingsScreen(name="settings"))

        self._build_nav_bar(root.ids.nav_bar, sm)
        return root

    def _build_nav_bar(self, nav_bar, sm):
        """يبني شريط تنقّل سفلي بسيط وملوّن بين الشاشات الأربع.
        Build a simple, colorful bottom nav bar between the 4 screens."""
        tabs = [
            ("المهام\nTodo", "todo", COLORS["primary"]),
            ("المواعيد\nCalendar", "calendar", COLORS["secondary"]),
            ("الصلاة\nPrayer", "prayer", COLORS["accent_teal"]),
            ("الإعدادات\nSettings", "settings", COLORS["primary_dark"]),
        ]
        for label, screen_name, color in tabs:
            btn = Button(text=label, background_color=color, color=(1, 1, 1, 1), font_size="12sp")
            btn.bind(on_release=lambda _b, s=screen_name: setattr(sm, "current", s))
            nav_bar.add_widget(btn)


if __name__ == "__main__":
    Mutaba3aApp().run()
