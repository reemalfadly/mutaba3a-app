# -*- coding: utf-8 -*-
"""نافذة اختيار مكان / Place picker dialog.

عربي: مكوّن (widget) يمكن استخدامه داخل أي شاشة: المستخدم يكتب اسم
      مكان، نضغط "بحث" فيستدعي app.geocode.geocode_place، ويعرض النتيجة
      (العنوان + الإحداثيات) مع زر "إرفاق" لحفظها في قاعدة البيانات
      المحلية وربطها بموعد.

English: A reusable widget: the user types a place name, presses
         "Search" which calls app.geocode.geocode_place, shows the
         result (address + coordinates) with an "Attach" button to
         save it locally and link it to an appointment.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from app.geocode import geocode_place
from app.db import get_db
from app.theme import COLORS


class PlacePickerPopup(Popup):
    """نافذة منبثقة لاختيار مكان وإرفاقه بموعد.
    Popup dialog to search a place and attach it to an appointment.

    Usage:
        PlacePickerPopup(on_attach=callback).open()
        callback receives the local place_id (int) once attached.
    """

    def __init__(self, on_attach=None, **kwargs):
        self.on_attach = on_attach
        self._result = None
        self.title = "اختيار مكان - Pick a place"
        self.size_hint = (0.9, 0.6)

        content = BoxLayout(orientation="vertical", spacing="8dp", padding="12dp")

        self.name_input = TextInput(hint_text="اكتب اسم المكان... / Type a place name...", multiline=False)
        content.add_widget(self.name_input)

        search_row = BoxLayout(size_hint_y=None, height="44dp", spacing="8dp")
        search_btn = Button(text="بحث / Search", background_color=COLORS["accent_teal"])
        search_btn.bind(on_release=self._do_search)
        search_row.add_widget(search_btn)
        content.add_widget(search_row)

        self.result_label = Label(
            text="", color=COLORS["text_primary"], halign="right", valign="middle",
        )
        self.result_label.bind(size=lambda inst, _v: setattr(inst, "text_size", inst.size))
        content.add_widget(self.result_label)

        bottom_row = BoxLayout(size_hint_y=None, height="44dp", spacing="8dp")
        self.attach_btn = Button(text="إرفاق / Attach", background_color=COLORS["primary"], disabled=True)
        self.attach_btn.bind(on_release=self._do_attach)
        cancel_btn = Button(text="إلغاء / Cancel", background_color=COLORS["text_muted"])
        cancel_btn.bind(on_release=self.dismiss)
        bottom_row.add_widget(self.attach_btn)
        bottom_row.add_widget(cancel_btn)
        content.add_widget(bottom_row)

        super().__init__(content=content, **kwargs)

    def _do_search(self, *_a):
        query = self.name_input.text.strip()
        result = geocode_place(query)
        if not result.ok:
            self.result_label.text = result.error
            self.attach_btn.disabled = True
            self._result = None
            return
        self._result = result
        self.result_label.text = (
            f"العنوان: {result.formatted_address}\n"
            f"الإحداثيات: {result.lat:.5f}, {result.lng:.5f}"
        )
        self.attach_btn.disabled = False

    def _do_attach(self, *_a):
        if not self._result:
            return
        db = get_db()
        place_id = db.add_place(
            name=self.name_input.text.strip(),
            formatted_address=self._result.formatted_address,
            lat=self._result.lat,
            lng=self._result.lng,
        )
        if self.on_attach:
            self.on_attach(place_id)
        self.dismiss()
