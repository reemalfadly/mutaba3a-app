# -*- coding: utf-8 -*-
"""
نظام الألوان (الثيم) / Theme & color palette
================================================

عربي: كل الألوان المستخدمة في التطبيق معرّفة هنا فقط، مرة وحدة، عشان
      يكون شكل التطبيق متناسق (بنفسجي/وردي/فيروزي/أصفر دافئ ومرح) وما
      نكرر أكواد الألوان بكل شاشة على حدة.

English: All app colors are defined here once so the look stays
         consistent (a bright, cheerful pink/purple/teal/warm-yellow
         palette) instead of scattering literal color codes per screen.

Use: from app.theme import COLORS, PALETTE_HEX, apply_kivymd_theme
"""

# RGBA tuples (0-1 range) for direct use in Kivy canvas / kv files.
COLORS = {
    "primary": (0.87, 0.36, 0.62, 1),        # وردي دافئ / warm pink
    "primary_dark": (0.62, 0.18, 0.45, 1),   # وردي غامق / deep pink
    "secondary": (0.55, 0.36, 0.86, 1),      # بنفسجي / purple
    "accent_teal": (0.20, 0.78, 0.72, 1),    # فيروزي / teal
    "accent_yellow": (1.0, 0.78, 0.24, 1),   # أصفر دافئ / warm yellow
    "background": (1.0, 0.96, 0.98, 1),      # وردي فاتح جداً للخلفية / very light pink bg
    "surface": (1.0, 1.0, 1.0, 1),           # أبيض للبطاقات / white cards
    "text_primary": (0.25, 0.15, 0.25, 1),   # بنفسجي غامق للنص / dark plum text
    "text_muted": (0.55, 0.48, 0.55, 1),
    "done": (0.20, 0.78, 0.55, 1),           # أخضر فيروزي لمهمة منجزة / green-teal for done
    "undone": (0.87, 0.36, 0.62, 1),         # وردي لمهمة غير منجزة / pink for not done
    "danger": (0.90, 0.30, 0.30, 1),         # أحمر للحذف/التحذير / red for delete/warning
    "warning": (1.0, 0.65, 0.20, 1),
    "white": (1, 1, 1, 1),
}

# Hex versions (handy for KivyMD theme_cls, which wants palette names or
# hex strings in some APIs) and for anything that needs a "#RRGGBB" string.
PALETTE_HEX = {
    "primary": "#DE5C9E",
    "primary_dark": "#9E2E73",
    "secondary": "#8C5CDB",
    "accent_teal": "#33C7B8",
    "accent_yellow": "#FFC73D",
    "background": "#FFF5F9",
    "surface": "#FFFFFF",
    "text_primary": "#402640",
    "text_muted": "#8C7A8C",
    "done": "#33C78C",
    "undone": "#DE5C9E",
    "danger": "#E64D4D",
    "warning": "#FFA633",
}

FONT_SIZE_TITLE = "22sp"
FONT_SIZE_NORMAL = "16sp"
FONT_SIZE_SMALL = "13sp"

RADIUS = 18  # corner radius used for cards/buttons -- friendly rounded look


def apply_kivymd_theme(md_app):
    """يهيّئ ثيم KivyMD بألوان التطبيق المرحة إن كانت KivyMD متوفرة.
    Configure the KivyMD theme_cls with our cheerful palette, if KivyMD
    is being used. Safe to call even if theme_cls has slightly different
    attributes across KivyMD versions (wrapped in try/except).
    """
    try:
        md_app.theme_cls.theme_style = "Light"
        # KivyMD ships a fixed set of named palette colors; "Pink" is the
        # closest built-in match to our custom warm pink/purple palette.
        md_app.theme_cls.primary_palette = "Pink"
        md_app.theme_cls.accent_palette = "Purple"
        try:
            md_app.theme_cls.primary_hue = "400"
        except Exception:
            pass
    except Exception:
        # KivyMD not available or API differs -- app still works,
        # screens fall back to plain Kivy colors from COLORS above.
        pass
