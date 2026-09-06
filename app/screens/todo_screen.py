# -*- coding: utf-8 -*-
"""شاشة قائمة المهام / Todo list screen.

عربي: عرض المهام، إضافة مهمة جديدة، تحديدها كمنجزة/غير منجزة، ترحيلها
      لتاريخ آخر، وحذفها. يستخدم KivyMD إن كانت متوفرة، وإلا يرجع
      لعناصر Kivy العادية ملوّنة يدوياً بنفس الثيم.

English: Shows tasks, lets the user add a new task, mark done/undone,
         postpone (reschedule) to another date, and delete. Uses
         KivyMD widgets when available, falling back to plain Kivy
         widgets styled with the shared theme.
"""

import datetime

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

from app.db import get_db
from app.theme import COLORS, PALETTE_HEX

KV = """
<TaskRow@BoxLayout>:
    size_hint_y: None
    height: "64dp"
    padding: "10dp", "6dp"
    spacing: "10dp"

<TodoScreen>:
    name: "todo"
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
                    rgba: app.theme_colors["primary"]
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "المهام - Todo"
                color: 1, 1, 1, 1
                font_size: "20sp"
                bold: True

        BoxLayout:
            size_hint_y: None
            height: "48dp"
            padding: "8dp", "4dp"
            spacing: "8dp"
            TextInput:
                id: new_task_input
                hint_text: "اكتب مهمة جديدة... / New task..."
                multiline: False
                on_text_validate: root.add_task()
            Button:
                text: "إضافة\\nAdd"
                size_hint_x: None
                width: "90dp"
                background_color: app.theme_colors["accent_teal"]
                on_release: root.add_task()

        ScrollView:
            BoxLayout:
                id: task_list
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


class TodoScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh()

    def add_task(self):
        text_input = self.ids.new_task_input
        title = text_input.text.strip()
        if not title:
            return
        db = get_db()
        db.add_task(title)
        text_input.text = ""
        self.refresh()

    def refresh(self):
        container = self.ids.task_list
        container.clear_widgets()
        db = get_db()
        tasks = db.list_tasks()
        if not tasks:
            container.add_widget(Label(
                text="لا توجد مهام بعد. أضف أول مهمة! / No tasks yet. Add your first one!",
                size_hint_y=None, height="60dp", color=COLORS["text_muted"],
            ))
            return
        for task in tasks:
            container.add_widget(self._build_row(task))

    def _build_row(self, task):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="72dp",
                         padding=("10dp", "6dp"), spacing="8dp")
        with row.canvas.before:
            Color(*COLORS["surface"])
            rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[14])
        def _update_rect(instance, _value, rect=rect):
            rect.pos = instance.pos
            rect.size = instance.size
        row.bind(pos=_update_rect, size=_update_rect)

        done = bool(task.get("done"))
        status_color = COLORS["done"] if done else COLORS["undone"]

        toggle_btn = Button(
            text="✓" if done else "○",
            size_hint_x=None, width="48dp",
            background_color=status_color,
            color=(1, 1, 1, 1),
        )
        toggle_btn.bind(on_release=lambda *_a, t=task: self._toggle_done(t))
        row.add_widget(toggle_btn)

        info = BoxLayout(orientation="vertical")
        title_text = task["title"]
        if done:
            title_text = f"[s]{title_text}[/s]"
        due = ""
        if task.get("due_date"):
            due = f"{task['due_date']} {task.get('due_time','')}".strip()
        info.add_widget(Label(
            text=title_text, markup=True, halign="right", valign="middle",
            color=COLORS["text_primary"], size_hint_y=0.6,
        ))
        info.add_widget(Label(
            text=(f"موعد: {due}" if due else "بدون تاريخ محدد"),
            halign="right", valign="middle", font_size="12sp",
            color=COLORS["text_muted"], size_hint_y=0.4,
        ))
        row.add_widget(info)

        postpone_btn = Button(text="ترحيل\nPostpone", size_hint_x=None, width="80dp",
                               background_color=COLORS["accent_yellow"])
        postpone_btn.bind(on_release=lambda *_a, t=task: self._open_postpone_dialog(t))
        row.add_widget(postpone_btn)

        delete_btn = Button(text="حذف\nDelete", size_hint_x=None, width="70dp",
                             background_color=COLORS["danger"])
        delete_btn.bind(on_release=lambda *_a, t=task: self._delete(t))
        row.add_widget(delete_btn)

        return row

    def _toggle_done(self, task):
        db = get_db()
        db.set_task_done(task["id"], not bool(task.get("done")))
        self.refresh()

    def _delete(self, task):
        db = get_db()
        db.delete_task(task["id"])
        self.refresh()

    def _open_postpone_dialog(self, task):
        content = BoxLayout(orientation="vertical", spacing="8dp", padding="12dp")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        date_input = TextInput(text=tomorrow, hint_text="YYYY-MM-DD", multiline=False)
        time_input = TextInput(text=task.get("due_time", "") or "09:00", hint_text="HH:MM", multiline=False)
        content.add_widget(Label(text="ترحيل المهمة إلى تاريخ / وقت جديد", color=COLORS["text_primary"],
                                  size_hint_y=None, height="30dp"))
        content.add_widget(Label(text="التاريخ (YYYY-MM-DD):", size_hint_y=None, height="24dp"))
        content.add_widget(date_input)
        content.add_widget(Label(text="الوقت (HH:MM):", size_hint_y=None, height="24dp"))
        content.add_widget(time_input)

        buttons = BoxLayout(size_hint_y=None, height="44dp", spacing="8dp")
        popup = Popup(title="ترحيل المهام - Postpone Task", content=content, size_hint=(0.85, 0.5))

        def do_postpone(*_a):
            db = get_db()
            db.postpone_task(task["id"], date_input.text.strip(), time_input.text.strip())
            popup.dismiss()
            self.refresh()

        confirm_btn = Button(text="تأكيد / Confirm", background_color=COLORS["primary"])
        confirm_btn.bind(on_release=do_postpone)
        cancel_btn = Button(text="إلغاء / Cancel", background_color=COLORS["text_muted"])
        cancel_btn.bind(on_release=popup.dismiss)
        buttons.add_widget(confirm_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)

        popup.open()
