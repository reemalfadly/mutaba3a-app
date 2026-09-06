# -*- coding: utf-8 -*-
"""شاشة المواعيد (تقويم) / Calendar / appointments screen.

عربي: إضافة/تعديل/حذف مواعيد بتاريخ ووقت، مع إمكانية ربط المكان
      (باستخدام PlacePickerPopup) اختيارياً بكل موعد.

English: Add/edit/delete appointments with a date & time, optionally
         linking a geocoded place to each one via PlacePickerPopup.
"""

import datetime

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle

from app.db import get_db
from app.theme import COLORS
from app.screens.place_picker import PlacePickerPopup

KV = """
<CalendarScreen>:
    name: "calendar"
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
                    rgba: app.theme_colors["secondary"]
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "المواعيد - Appointments"
                color: 1, 1, 1, 1
                font_size: "20sp"
                bold: True

        BoxLayout:
            size_hint_y: None
            height: "48dp"
            padding: "8dp", "4dp"
            Button:
                text: "+ إضافة موعد جديد / Add appointment"
                background_color: app.theme_colors["accent_yellow"]
                on_release: root.open_add_dialog()

        ScrollView:
            BoxLayout:
                id: appt_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: "6dp"
                spacing: "8dp"
"""

try:
    Builder.load_string(KV)
except Exception:
    pass


class CalendarScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        container = self.ids.appt_list
        container.clear_widgets()
        db = get_db()
        appts = db.list_appointments()
        if not appts:
            container.add_widget(Label(
                text="لا توجد مواعيد بعد / No appointments yet",
                size_hint_y=None, height="60dp", color=COLORS["text_muted"],
            ))
            return
        for appt in appts:
            container.add_widget(self._build_row(appt))

    def _build_row(self, appt):
        db = get_db()
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="80dp",
                         padding=("10dp", "6dp"), spacing="8dp")
        with row.canvas.before:
            Color(*COLORS["surface"])
            rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[14])
        def _update_rect(instance, _value, rect=rect):
            rect.pos = instance.pos
            rect.size = instance.size
        row.bind(pos=_update_rect, size=_update_rect)

        info = BoxLayout(orientation="vertical")
        info.add_widget(Label(
            text=appt["title"], halign="right", valign="middle",
            color=COLORS["text_primary"], font_size="16sp", bold=True, size_hint_y=0.4,
        ))
        when = f"{appt['date']} {appt.get('time','')}".strip()
        info.add_widget(Label(
            text=f"الموعد: {when}", halign="right", valign="middle",
            color=COLORS["text_muted"], font_size="12sp", size_hint_y=0.3,
        ))
        place_text = "بدون مكان محدد / No place attached"
        if appt.get("place_id"):
            place = db.get_place(appt["place_id"])
            if place:
                place_text = f"📍 {place['name']} - {place.get('formatted_address','')}"
        info.add_widget(Label(
            text=place_text, halign="right", valign="middle",
            color=COLORS["accent_teal"], font_size="11sp", size_hint_y=0.3,
        ))
        row.add_widget(info)

        delete_btn = Button(text="حذف\nDelete", size_hint_x=None, width="70dp",
                             background_color=COLORS["danger"])
        delete_btn.bind(on_release=lambda *_a, a=appt: self._delete(a))
        row.add_widget(delete_btn)

        return row

    def _delete(self, appt):
        db = get_db()
        db.delete_appointment(appt["id"])
        self.refresh()

    def open_add_dialog(self):
        content = BoxLayout(orientation="vertical", spacing="8dp", padding="12dp")
        today = datetime.date.today().isoformat()

        title_input = TextInput(hint_text="عنوان الموعد / Appointment title", multiline=False)
        date_input = TextInput(text=today, hint_text="YYYY-MM-DD", multiline=False)
        time_input = TextInput(text="09:00", hint_text="HH:MM", multiline=False)
        notes_input = TextInput(hint_text="ملاحظات (اختياري) / Notes (optional)", multiline=False)

        content.add_widget(Label(text="عنوان الموعد:", size_hint_y=None, height="22dp"))
        content.add_widget(title_input)
        content.add_widget(Label(text="التاريخ (YYYY-MM-DD):", size_hint_y=None, height="22dp"))
        content.add_widget(date_input)
        content.add_widget(Label(text="الوقت (HH:MM):", size_hint_y=None, height="22dp"))
        content.add_widget(time_input)
        content.add_widget(Label(text="ملاحظات:", size_hint_y=None, height="22dp"))
        content.add_widget(notes_input)

        state = {"place_id": None}
        place_status = Label(text="لم يتم إرفاق مكان / No place attached", size_hint_y=None,
                              height="22dp", color=COLORS["text_muted"])

        def open_place_picker(*_a):
            def on_attach(place_id):
                state["place_id"] = place_id
                place = get_db().get_place(place_id)
                place_status.text = f"📍 {place['name']}" if place else "تم الإرفاق"
            PlacePickerPopup(on_attach=on_attach).open()

        place_btn = Button(text="ربط مكان (اختياري) / Attach place (optional)",
                            size_hint_y=None, height="40dp", background_color=COLORS["accent_teal"])
        place_btn.bind(on_release=open_place_picker)
        content.add_widget(place_btn)
        content.add_widget(place_status)

        buttons = BoxLayout(size_hint_y=None, height="44dp", spacing="8dp")
        popup = Popup(title="موعد جديد - New Appointment", content=content, size_hint=(0.9, 0.85))

        def do_save(*_a):
            title = title_input.text.strip()
            if not title:
                return
            db = get_db()
            db.add_appointment(
                title=title,
                date=date_input.text.strip(),
                time=time_input.text.strip(),
                notes=notes_input.text.strip(),
                place_id=state["place_id"],
            )
            popup.dismiss()
            self.refresh()

        save_btn = Button(text="حفظ / Save", background_color=COLORS["primary"])
        save_btn.bind(on_release=do_save)
        cancel_btn = Button(text="إلغاء / Cancel", background_color=COLORS["text_muted"])
        cancel_btn.bind(on_release=popup.dismiss)
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)

        popup.open()
