#!/usr/bin/env python3
#
# =============================================================================
#  Project      : WRCPlayer
#  Description  : WRCPlayer - Media Player Ocx o Qtlibray o Demo
#  Author       : Raffaele Catapano
#  License      : MIT (see LICENSE)
#  Created on   : 25/11/2026
#  Version      : 1.6
#
#  Copyright (c) 2025-2026 Raffaele Catapano
#  Released under the MIT License - see the LICENSE file for details.
#  SPDX-License-Identifier: MIT
# =============================================================================

import random

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

# ---------------------------------------------------------------------------
# Palette "hardware" anni 2000: metallo grafite, arancio WMP, LCD ambra.
# ---------------------------------------------------------------------------
ACCENT = "#f2801e"          # arancio classico (riempimento slider, LED attivi)
ACCENT_DARK = "#b85c00"
ACCENT_HI = "#ffb054"

LCD_BG = "#0d0b06"          # schermo spento
LCD_GLOW = "#ffcf80"        # testo acceso
LCD_GLOW_SOFT = "#e8a44a"
LCD_DIM = "#8a744f"

METAL_HI = "#b9bfc8"
METAL_MID = "#7c828b"
METAL_LOW = "#464a52"
METAL_DARK = "#2a2d33"

BG_TOP = "#2e3138"
BG_BOTTOM = "#101114"

PANEL_TEXT = "#cfc7b8"
PANEL_DIM = "#8f959e"

FONT_UI = ["Segoe UI", "Noto Sans", "DejaVu Sans", "sans-serif"]
FONT_MONO = ["Consolas", "DejaVu Sans Mono", "Liberation Mono", "monospace"]

# ---------------------------------------------------------------------------
# QSS di contorno (tooltip, menu, pulsanti "meccanici" testuali).
# ---------------------------------------------------------------------------
APP_QSS = """
QToolTip {
    background: #14151a; color: %(accent_hi)s;
    border: 1px solid #3a3d44; padding: 4px 7px; font-size: 12px;
}
QMenu {
    background: #1d1f24; color: #d8d3c8;
    border: 1px solid #0b0c0f; padding: 4px;
}
QMenu::item:selected { background: %(accent)s; color: #141519; }
"""

METAL_BUTTON_QSS = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8d939c, stop:0.45 #5f646c, stop:1 #3a3e45);
    color: #17191d;
    border: 1px solid #23262b;
    border-top: 1px solid #a2a8b1;
    border-left: 1px solid #8f959e;
    border-radius: 4px;
    padding: 5px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #a2a8b1, stop:0.45 #6e747d, stop:1 #464a52);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a3e45, stop:1 #55595f);
    padding-top: 6px;
}
"""


def apply_app_qss(app):
    """Applica il QSS globale (tooltip, menu)."""
    app.setStyleSheet(APP_QSS % {"accent": ACCENT, "accent_hi": ACCENT_HI})


# ---------------------------------------------------------------------------
# Texture "metallo spazzolato": linee orizzontali sottili su gradiente.
# ---------------------------------------------------------------------------
_BRUSH_CACHE = {}


def brushed_tile(w=256, h=256, seed=7):
    """Ritorna un QPixmap 256x256 di metallo spazzolato (tileabile)."""
    key = (w, h, seed)
    if key in _BRUSH_CACHE:
        return _BRUSH_CACHE[key]
    pm = QPixmap(w, h)
    pm.fill(QColor(BG_TOP))
    p = QPainter(pm)
    p.fillRect(0, 0, w, h, QColor(BG_TOP))
    rng = random.Random(seed)
    for y in range(h):
        # gradiente verticale leggero per profondita'
        t = y / h
        base = QColor(BG_TOP)
        c = base.lighter(100 + int(40 * (1 - t)))
        p.setPen(c)
        p.drawLine(0, y, w, y)
    # grana: linee orizzontali chiare/scuri random
    for _ in range(h * 3):
        y = rng.randrange(h)
        a = rng.randint(4, 16)
        if rng.random() < 0.5:
            col = QColor(255, 255, 255, a)
        else:
            col = QColor(0, 0, 0, a + 6)
        p.setPen(col)
        x = rng.randrange(w)
        ln = rng.randint(8, 90)
        p.drawLine(x, y, min(w, x + ln), y)
    p.end()
    _BRUSH_CACHE[key] = pm
    return pm


def bevel_frame(p, rect, radius=6.0, hi=Qt.GlobalColor.white, hi_a=28,
                lo="#000000", lo_a=150, width=1.0):
    """Bordo a sbalzo: lato in alto/sinistra chiaro, in basso/destra scuro."""
    p.save()
    pen_hi = QColor(hi)
    pen_hi.setAlpha(hi_a)
    pen_lo = QColor(lo)
    pen_lo.setAlpha(lo_a)
    r = QRectF(rect)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    p.setPen(pen_hi)
    p.drawLine(int(r.left()), int(r.top()), int(r.right()), int(r.top()))
    p.drawLine(int(r.left()), int(r.top()), int(r.left()), int(r.bottom()))
    p.setPen(pen_lo)
    p.drawLine(int(r.left()), int(r.bottom()), int(r.right()), int(r.bottom()))
    p.drawLine(int(r.right()), int(r.top()), int(r.right()), int(r.bottom()))
    p.restore()


def draw_screws(p, rect, inset=9):
    """Vitette angolari decorative su un pannello."""
    r = QRectF(rect)
    cx = [r.left() + inset, r.right() - inset]
    cy = [r.top() + inset, r.bottom() - inset]
    for x in cx:
        for y in cy:
            from PySide6.QtGui import QRadialGradient
            g = QRadialGradient(x + 0.5, y + 0.2, 4.6)
            g.setColorAt(0.0, QColor("#c8cdd4"))
            g.setColorAt(0.7, QColor("#5c6169"))
            g.setColorAt(1.0, QColor("#22252a"))
            p.save()
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setPen(QColor(0, 0, 0, 120))
            p.setBrush(g)
            p.drawEllipse(QRectF(x - 4.0, y - 4.0, 8.0, 8.0))
            p.setPen(QColor(30, 32, 36, 210))
            import math
            ang = (x + y) % 180
            dx = math.cos(math.radians(ang)) * 2.8
            dy = math.sin(math.radians(ang)) * 2.8
            p.drawLine(int(x - dx), int(y - dy), int(x + dx), int(y + dy))
            p.restore()
