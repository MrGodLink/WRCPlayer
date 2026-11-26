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

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QConicalGradient, QFont, QLinearGradient,
                           QPainter, QPainterPath, QPen, QRadialGradient)
from PySide6.QtWidgets import QAbstractButton, QSlider, QStyle, QLabel, QWidget

import theme

# ---------------------------------------------------------------------------
# Glifi (vettoriali, disegnati su una griglia 24x24)
# ---------------------------------------------------------------------------
PLAY, PAUSE, STOP, PREV, NEXT = "play", "pause", "stop", "prev", "next"
SPEAKER, SPEAKER_MUTE = "speaker", "mute"
FOLDER, OPEN_FILE, LIST, MONITOR = "folder", "open", "list", "monitor"
SHUFFLE, REPEAT, REPEAT_ONE = "shuffle", "repeat", "repeat_one"
PIN, FULLSCREEN, PLUS, MINUS = "pin", "full", "plus", "minus"


def _paint_glyph(p, kind, rect, color, color_hi=None):
    """Disegna un glifo dentro `rect` (scala dal disegno 24x24)."""
    s = min(rect.width(), rect.height()) / 24.0
    p.save()
    p.translate(rect.x() + (rect.width() - 24 * s) / 2.0,
                rect.y() + (rect.height() - 24 * s) / 2.0)
    p.scale(s, s)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    main = QColor(color)
    hi = QColor(color_hi) if color_hi else main

    path = QPainterPath()
    strokes = []  # (path, width)

    def R(x, y, w, h):
        return QRectF(x, y, w, h)

    if kind == PLAY:
        path.moveTo(7, 4); path.lineTo(20.5, 12); path.lineTo(7, 20)
        path.closeSubpath()
    elif kind == PAUSE:
        path.addRoundedRect(R(6.5, 5, 4.2, 14), 1.6, 1.6)
        path.addRoundedRect(R(13.3, 5, 4.2, 14), 1.6, 1.6)
    elif kind == STOP:
        path.addRoundedRect(R(6.5, 6.5, 11, 11), 2, 2)
    elif kind == PREV:
        path.addRoundedRect(R(4.5, 5.5, 3.4, 13), 1.4, 1.4)
        tri = QPainterPath()
        tri.moveTo(19.5, 5.5); tri.lineTo(9.5, 12); tri.lineTo(19.5, 18.5)
        tri.closeSubpath()
        path = path.united(tri)
    elif kind == NEXT:
        path.addRoundedRect(R(16.1, 5.5, 3.4, 13), 1.4, 1.4)
        tri = QPainterPath()
        tri.moveTo(4.5, 5.5); tri.lineTo(14.5, 12); tri.lineTo(4.5, 18.5)
        tri.closeSubpath()
        path = path.united(tri)
    elif kind in (SPEAKER, SPEAKER_MUTE):
        path.moveTo(3.5, 9); path.lineTo(7.5, 9); path.lineTo(12.5, 4.5)
        path.lineTo(12.5, 19.5); path.lineTo(7.5, 15); path.lineTo(3.5, 15)
        path.closeSubpath()
        if kind == SPEAKER:
            arc = QPainterPath()
            arc.moveTo(15.0, 8.6)
            arc.quadTo(17.4, 12, 15.0, 15.4)
            strokes.append((arc, 1.8))
            arc2 = QPainterPath()
            arc2.moveTo(17.6, 6.6)
            arc2.quadTo(21.2, 12, 17.6, 17.4)
            strokes.append((arc2, 1.8))
        else:
            for x1, y1 in ((15.2, 9.2), (19.6, 13.6)):
                ln = QPainterPath()
                ln.moveTo(x1, y1); ln.lineTo(x1 + 4.4, y1 + 4.4)
                strokes.append((ln, 2.0))
                ln2 = QPainterPath()
                ln2.moveTo(x1 + 4.4, y1); ln2.lineTo(x1, y1 + 4.4)
                strokes.append((ln2, 2.0))
    elif kind == FOLDER:
        path.moveTo(3.5, 6); path.lineTo(9.2, 6); path.lineTo(11.2, 8.2)
        path.lineTo(20.5, 8.2); path.lineTo(20.5, 18.5); path.lineTo(3.5, 18.5)
        path.closeSubpath()
    elif kind == OPEN_FILE:
        doc = QPainterPath()
        doc.addRoundedRect(R(5.5, 3.5, 13, 17), 1.8, 1.8)
        strokes.append((doc, 1.8))
        for yy in (7.5, 11, 14.5):
            ln = QPainterPath()
            ln.moveTo(8.2, yy); ln.lineTo(15.8, yy)
            strokes.append((ln, 1.6))
    elif kind == LIST:
        tri = QPainterPath()
        tri.moveTo(3.5, 7.5); tri.lineTo(10, 12); tri.lineTo(3.5, 16.5)
        tri.closeSubpath()
        path.addPath(tri)
        for yy in (7.5, 12, 16.5):
            ln = QPainterPath()
            ln.moveTo(12.8, yy); ln.lineTo(20.5, yy)
            strokes.append((ln, 1.9))
    elif kind == MONITOR:
        m = QPainterPath()
        m.addRoundedRect(R(3.5, 4.5, 17, 11.5), 1.8, 1.8)
        strokes.append((m, 1.8))
        st = QPainterPath()
        st.moveTo(12, 16); st.lineTo(12, 19.4)
        strokes.append((st, 1.8))
        base = QPainterPath()
        base.moveTo(8, 19.4); base.lineTo(16, 19.4)
        strokes.append((base, 1.8))
    elif kind == SHUFFLE:
        a = QPainterPath()
        a.moveTo(3.5, 7.5); a.lineTo(8, 7.5); a.lineTo(19.5, 16.5)
        strokes.append((a, 1.9))
        b = QPainterPath()
        b.moveTo(3.5, 16.5); b.lineTo(8, 16.5); b.lineTo(19.5, 7.5)
        strokes.append((b, 1.9))
        ar1 = QPainterPath()
        ar1.moveTo(16.6, 16.9); ar1.lineTo(20.2, 17.0); ar1.lineTo(19.6, 13.2)
        ar1.closeSubpath(); path.addPath(ar1)
        ar2 = QPainterPath()
        ar2.moveTo(16.6, 7.1); ar2.lineTo(20.2, 7.0); ar2.lineTo(19.6, 10.8)
        ar2.closeSubpath(); path.addPath(ar2)
    elif kind in (REPEAT, REPEAT_ONE):
        cx, cy, rx, ry = 12.0, 12.0, 6.6, 5.4
        import math
        a1 = QPainterPath()
        # arco superiore da 160° a 20° (angoli Qt: 0°=ore 3, senso antiorario)
        a1.arcMoveTo(R(cx - rx, cy - ry, 2 * rx, 2 * ry), 160)
        a1.arcTo(R(cx - rx, cy - ry, 2 * rx, 2 * ry), 160, -140)
        strokes.append((a1, 1.9))
        a2 = QPainterPath()
        a2.arcMoveTo(R(cx - rx, cy - ry, 2 * rx, 2 * ry), -20)
        a2.arcTo(R(cx - rx, cy - ry, 2 * rx, 2 * ry), -20, -140)
        strokes.append((a2, 1.9))
        # punte di freccia
        ax, ay = cx + rx * math.cos(math.radians(20)), cy - ry * math.sin(math.radians(20))
        tip = QPainterPath()
        tip.moveTo(ax + 2.6, ay + 2.9); tip.lineTo(ax - 2.4, ay + 3.6)
        tip.lineTo(ax - 1.6, ay - 0.6); tip.closeSubpath(); path.addPath(tip)
        if kind == REPEAT_ONE:
            f = QFont()
            f.setFamilies(theme.FONT_MONO)
            f.setPixelSize(10)
            f.setBold(True)
            p.setFont(f)
        else:
            p.setFont(QFont())
    elif kind == PIN:
        path.addEllipse(QPointF(12, 6.2), 3.0, 3.0)
        body = QPainterPath()
        body.moveTo(8.6, 7.4); body.lineTo(15.4, 7.4); body.lineTo(13.4, 12.4)
        body.lineTo(10.6, 12.4); body.closeSubpath()
        path.addPath(body)
        needle = QPainterPath()
        needle.moveTo(12, 12.4); needle.lineTo(12, 19.5)
        strokes.append((needle, 1.6))
    elif kind == FULLSCREEN:
        for x, y, dx, dy in ((4, 4, 1, 1), (20, 4, -1, 1),
                             (4, 20, 1, -1), (20, 20, -1, -1)):
            corner = QPainterPath()
            corner.moveTo(x + dx * 4.6, y)
            corner.lineTo(x, y)
            corner.lineTo(x, y + dy * 4.6)
            strokes.append((corner, 2.0))
    elif kind == PLUS:
        a = QPainterPath(); a.moveTo(12, 6.5); a.lineTo(12, 17.5)
        strokes.append((a, 2.4))
        b = QPainterPath(); b.moveTo(6.5, 12); b.lineTo(17.5, 12)
        strokes.append((b, 2.4))
    elif kind == MINUS:
        b = QPainterPath(); b.moveTo(6.5, 12); b.lineTo(17.5, 12)
        strokes.append((b, 2.4))

    # riempimento con ombra incisa (offset chiaro sotto)
    if not path.isEmpty():
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 42))
        p.drawPath(path.translated(0, 1.1))
        p.setBrush(main)
        p.drawPath(path)
    if strokes:
        pen = QPen(hi, 1.0)
        for sp, w in strokes:
            pen.setWidthF(w)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(QPen(QColor(255, 255, 255, 42), w + 1.1,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
            p.drawPath(sp.translated(0, 1.1))
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(sp)
    if kind == REPEAT_ONE:
        p.setPen(QPen(QColor(255, 255, 255, 42), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setFont(QFont())  # ristabilisce
    p.restore()


def _mono_font(px, bold=False):
    f = QFont()
    f.setFamilies(theme.FONT_MONO)
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def _ui_font(px, bold=False, spacing=0.0):
    f = QFont()
    f.setFamilies(theme.FONT_UI)
    f.setPixelSize(px)
    f.setBold(bold)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


# ---------------------------------------------------------------------------
# Pannello principale in metallo spazzolato
# ---------------------------------------------------------------------------
class BrushedPanel(QWidget):
    """Sfondo in metallo spazzolato con bordo a sbalzo (central widget)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tile = None

    def paintEvent(self, ev):
        p = QPainter(self)
        if self._tile is None or self._tile.width() != self.width():
            self._tile = theme.brushed_tile()
        p.drawTiledPixmap(self.rect(), self._tile)
        # gradiente verticale di riflesso
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor(255, 255, 255, 16))
        g.setColorAt(0.35, QColor(255, 255, 255, 0))
        g.setColorAt(1.0, QColor(0, 0, 0, 70))
        p.fillRect(self.rect(), g)
        theme.bevel_frame(p, self.rect().adjusted(0, 0, -1, -1),
                          hi_a=36, lo_a=180)
        p.end()


# ---------------------------------------------------------------------------
# Bottoni in metallo
# ---------------------------------------------------------------------------
class MetalButton(QAbstractButton):
    """Pulsante circolare cromato con glifo inciso.

    accent=True aggiunge un LED arancio acceso quando il bottone e'
    checked (mute, shuffle, repeat, sempre in primo piano...).
    """

    def __init__(self, glyph, diameter=44, accent=False, checkable=False,
                 tooltip="", parent=None):
        super().__init__(parent)
        self._glyph = glyph
        self._d = diameter
        self._accent = accent
        self.setCheckable(checkable)
        if tooltip:
            self.setToolTip(tooltip)
        self.setFixedSize(diameter, diameter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def set_glyph(self, g):
        if g != self._glyph:
            self._glyph = g
            self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        d = self._d
        r = d / 2.0 - 1.0
        cx, cy = d / 2.0, d / 2.0
        pressed = self.isDown()
        checked = self.isChecked()
        hover = self.underMouse() and self.isEnabled()

        # ombra esterna
        if not pressed:
            g = QRadialGradient(QPointF(cx, cy), r + 3)
            g.setColorAt(0.82, QColor(0, 0, 0, 0))
            g.setColorAt(0.94, QColor(0, 0, 0, 90))
            g.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g)
            p.drawRect(self.rect())

        # ghiera cromata
        g_ring = QConicalGradient(QPointF(cx, cy), 25)
        for stop, col in ((0.0, "#eef0f3"), (0.2, "#7e838b"),
                          (0.35, "#dde0e4"), (0.55, "#565b62"),
                          (0.75, "#c8ccd2"), (0.9, "#61666d"),
                          (1.0, "#eef0f3")):
            g_ring.setColorAt(stop, QColor(col))
        if checked:
            g_ring = QConicalGradient(QPointF(cx, cy), 25)
            g_ring.setColorAt(0.0, QColor("#ffcf8e"))
            g_ring.setColorAt(0.5, QColor("#b86410"))
            g_ring.setColorAt(1.0, QColor("#ffcf8e"))
        p.setPen(QPen(QColor(8, 9, 12, 190), 1.0))
        p.setBrush(g_ring)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # faccia
        g_face = QRadialGradient(QPointF(cx, cy - r * 0.35), r * 1.15)
        if pressed:
            g_face.setColorAt(0.0, QColor("#3d4149"))
            g_face.setColorAt(1.0, QColor("#22252b"))
        elif checked:
            g_face.setColorAt(0.0, QColor("#6a6154"))
            g_face.setColorAt(1.0, QColor("#3a3833"))
        else:
            g_face.setColorAt(0.0, QColor("#9aa1ab"))
            g_face.setColorAt(0.75, QColor("#5a5f67"))
            g_face.setColorAt(1.0, QColor("#393d44"))
        p.setPen(QPen(QColor(0, 0, 0, 60), 0.8))
        p.setBrush(g_face)
        p.drawEllipse(QPointF(cx, cy), r - 1.6, r - 1.6)

        # riflesso lucido (metà superiore)
        gloss = QPainterPath()
        gloss.moveTo(cx - (r - 2), cy)
        gloss.quadTo(cx, cy - 2.2 * r, cx + (r - 2), cy)
        gloss.quadTo(cx, cy - r * 0.55, cx - (r - 2), cy)
        gloss.closeSubpath()
        p.fillPath(gloss, QColor(255, 255, 255, 44 if not pressed else 16))

        if hover and not pressed:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 18))
            p.drawEllipse(QPointF(cx, cy), r - 2, r - 2)

        # glifo
        gs = d * (0.54 if self._d <= 40 else 0.5)
        col = QColor("#f2ede2") if (pressed or checked) else QColor("#17191d")
        if not self.isEnabled():
            col = QColor("#84878d")
        rect = QRectF(cx - gs / 2, cy - gs / 2 + (1.0 if pressed else 0.0),
                      gs, gs)
        _paint_glyph(p, self._glyph, rect, col,
                     QColor("#5c6168") if col == QColor("#17191d") else None)

        # LED accent se checked
        if self._accent and checked:
            ly = cy + r * 0.62
            g_led = QRadialGradient(QPointF(cx, ly), 5)
            g_led.setColorAt(0.0, QColor("#ffe2b0"))
            g_led.setColorAt(0.4, QColor(theme.ACCENT))
            g_led.setColorAt(1.0, QColor(theme.ACCENT_DARK))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g_led)
            p.drawEllipse(QPointF(cx, ly), 3.4, 3.4)
        p.end()


class MetalSlider(QSlider):
    """Cursore orizzontale: binario incassato, riempimento arancio lucido,
    manopola metallica zigrinata."""

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setRange(0, 1000)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        if (e.button() == Qt.MouseButton.LeftButton
                and self.orientation() == Qt.Orientation.Horizontal):
            v = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(),
                                               int(e.position().x()),
                                               self.width())
            self.setValue(v)
            e.accept()
        super().mousePressEvent(e)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        groove_h = 10.0
        gy = (h - groove_h) / 2.0
        groove = QRectF(2, gy, w - 4, groove_h)

        # binario incassato con bordo leggibile sul metallo
        outer = groove.adjusted(-1, -1, 1, 1)
        p.setPen(QPen(QColor(255, 255, 255, 42), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(outer, 5, 5)
        g_in = QLinearGradient(0, groove.top(), 0, groove.bottom())
        g_in.setColorAt(0.0, QColor(0, 0, 0, 200))
        g_in.setColorAt(0.25, QColor(16, 18, 22))
        g_in.setColorAt(1.0, QColor("#3a3f47"))
        p.setPen(QPen(QColor(0, 0, 0, 190), 1))
        p.setBrush(g_in)
        p.drawRoundedRect(groove, 4, 4)
        p.setPen(QPen(QColor(255, 255, 255, 34), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(int(groove.left() + 2), int(groove.bottom()),
                   int(groove.right() - 2), int(groove.bottom()))

        # riempimento
        ratio = (self.value() - self.minimum()) / max(
            1, self.maximum() - self.minimum())
        fill_w = max(0.0, (groove.width() - groove_h) * ratio) + groove_h
        if fill_w > 1:
            fill = QRectF(groove.left(), groove.top(),
                          min(fill_w, groove.width()), groove.height())
            g_fill = QLinearGradient(0, fill.top(), 0, fill.bottom())
            g_fill.setColorAt(0.0, QColor(theme.ACCENT_HI))
            g_fill.setColorAt(0.5, QColor(theme.ACCENT))
            g_fill.setColorAt(1.0, QColor(theme.ACCENT_DARK))
            p.setPen(QPen(QColor(0, 0, 0, 110), 1))
            p.setBrush(g_fill)
            p.drawRoundedRect(fill, 4, 4)
            g_hi = QLinearGradient(0, fill.top(), 0, fill.center().y())
            g_hi.setColorAt(0.0, QColor(255, 255, 255, 90))
            g_hi.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(g_hi)
            p.drawRoundedRect(fill.adjusted(2, 1.4, -2, -1.6), 3, 3)

        # manopola
        hx = groove.left() + (groove.width() - 14) * ratio
        knob = QRectF(hx, gy - 7.0, 14.0, groove_h + 14.0)
        g_k = QLinearGradient(knob.left(), knob.top(),
                              knob.left() + knob.width(), knob.bottom())
        for stop, col in ((0.0, "#e8ebef"), (0.35, "#9ba1aa"),
                          (0.62, "#6b7079"), (1.0, "#43474e")):
            g_k.setColorAt(stop, QColor(col))
        p.setPen(QPen(QColor(10, 12, 15, 210), 1))
        p.setBrush(g_k)
        p.drawRoundedRect(knob, 3.2, 3.2)
        p.setPen(QPen(QColor(30, 33, 38, 190), 1))
        for i in (0.28, 0.5, 0.72):
            x = knob.left() + knob.width() * i
            p.drawLine(int(x), int(knob.top() + 3),
                       int(x), int(knob.bottom() - 3))
        p.setPen(QPen(QColor(255, 255, 255, 70), 1))
        p.drawLine(int(knob.left() + 2), int(knob.top() + 1),
                   int(knob.right() - 2), int(knob.top() + 1))
        p.end()


# ---------------------------------------------------------------------------
# VU analogico
# ---------------------------------------------------------------------------
class VuDial(QWidget):
    """Dial VU analogico: ghiera cromata, quadrante crema, ago rosso."""

    def __init__(self, label="L", parent=None):
        super().__init__(parent)
        self._label = label
        self._level = 0.0
        self.setFixedSize(84, 84)

    def set_level(self, v):
        self._level = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = self.width() / 2.0 - 4.0
        c = QPointF(self.width() / 2, self.height() / 2 + 3)

        # ghiera
        g_ring = QConicalGradient(c, 30)
        for stop, col in ((0.0, "#d9dce1"), (0.25, "#6f747c"),
                          (0.5, "#c7cbd1"), (0.75, "#4b4f56"),
                          (1.0, "#d9dce1")):
            g_ring.setColorAt(stop, QColor(col))
        p.setPen(QPen(QColor(8, 9, 12, 190), 1))
        p.setBrush(g_ring)
        p.drawEllipse(c, r, r)

        # quadrante crema
        g_face = QRadialGradient(QPointF(c.x(), c.y() - 14), r)
        g_face.setColorAt(0.0, QColor("#f6ecd4"))
        g_face.setColorAt(0.85, QColor("#e2d3ac"))
        g_face.setColorAt(1.0, QColor("#b9a67d"))
        p.setBrush(g_face)
        p.setPen(QPen(QColor(60, 50, 30, 160), 1))
        p.drawEllipse(c, r - 4, r - 4)

        # scala: da -50° a +50°
        import math
        a0, a1 = -52.0, 52.0
        p.setPen(QPen(QColor("#4a3c22"), 1.2))
        for i in range(11):
            t = i / 10.0
            ang = math.radians(a0 + (a1 - a0) * t)
            rr0 = r - 8 if i % 5 else r - 11
            x0 = c.x() + math.sin(ang) * rr0
            y0 = c.y() - math.cos(ang) * rr0
            x1 = c.x() + math.sin(ang) * (r - 14)
            y1 = c.y() - math.cos(ang) * (r - 14)
            p.drawLine(int(x0), int(y0), int(x1), int(y1))

        # zona rossa finale
        p.setPen(QPen(QColor("#b3341e"), 3.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        import math as _m
        span = (a1 - a0)
        rect = QRectF(c.x() - (r - 16), c.y() - (r - 16),
                      2 * (r - 16), 2 * (r - 16))
        start_q = int((90 + a0 + span * 0.78) * 16)
        span_q = int(-span * 0.22 * 16)
        p.drawArc(rect, start_q, span_q)

        # ago
        ang = math.radians(a0 + (a1 - a0) * self._level)
        tip_x = c.x() + math.sin(ang) * (r - 15)
        tip_y = c.y() - math.cos(ang) * (r - 15)
        p.setPen(QPen(QColor(0, 0, 0, 70), 3.4))
        p.drawLine(int(c.x() + 1.5), int(c.y() + 1.5), int(tip_x + 1.5), int(tip_y + 1.5))
        p.setPen(QPen(QColor("#8f2418"), 2.4))
        p.drawLine(int(c.x()), int(c.y()), int(tip_x), int(tip_y))

        # perno
        g_piv = QRadialGradient(c, 6)
        g_piv.setColorAt(0.0, QColor("#d8d3c8"))
        g_piv.setColorAt(1.0, QColor("#55504a"))
        p.setPen(QPen(QColor(0, 0, 0, 130), 1))
        p.setBrush(g_piv)
        p.drawEllipse(c, 5.0, 5.0)

        # etichetta
        p.setFont(_ui_font(9, bold=True, spacing=1.0))
        p.setPen(QPen(QColor("#6d5c3a")))
        p.drawText(QRectF(c.x() - 20, c.y() + 8, 40, 14),
                   Qt.AlignmentFlag.AlignCenter, self._label)

        # riflesso vetro
        g_glass = QLinearGradient(0, c.y() - r, 0, c.y())
        g_glass.setColorAt(0.0, QColor(255, 255, 255, 60))
        g_glass.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g_glass)
        p.drawEllipse(QRectF(c.x() - (r - 5), c.y() - (r - 4),
                             2 * (r - 5), (r - 4)))
        p.end()


# ---------------------------------------------------------------------------
# Display LCD/VFD
# ---------------------------------------------------------------------------
class LcdDisplay(QWidget):
    """Schermo LCD ambra incassato: tempo grande, brano, stato, badge e VU."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._track = "Nessun brano"
        self._pos = 0.0
        self._dur = 0.0
        self._state_text = "Pronto"
        self._state_kind = "stop"
        self._rate = 1.0
        self._shuffle = False
        self._repeat = "off"
        self._muted = False
        self._compact = False
        self._hint = None
        self._vu_l = VuDial("L", self)
        self._vu_r = VuDial("R", self)
        self._relayout()

    # --- API ----------------------------------------------------------------
    def set_track(self, s):
        self._track = s or "Nessun brano"
        self.update()

    def set_time(self, pos, dur):
        self._pos, self._dur = pos, dur
        self.update()

    def set_state(self, text, kind):
        self._state_text, self._state_kind = text, kind
        self.update()

    def set_rate(self, r):
        self._rate = r
        self.update()

    def set_shuffle(self, b):
        self._shuffle = b
        self.update()

    def set_repeat(self, mode):
        self._repeat = mode
        self.update()

    def set_muted(self, b):
        self._muted = b
        self.update()

    def set_hint(self, s):
        self._hint = s
        self.update()

    def set_vu(self, l, r):
        self._vu_l.set_level(l)
        self._vu_r.set_level(r)

    def set_compact(self, b):
        self._compact = b
        self.setFixedHeight(84 if b else 132)
        self._relayout()
        self.update()

    def is_compact(self):
        return self._compact

    def _relayout(self):
        if self._compact:
            self._vu_l.hide(); self._vu_r.hide()
        else:
            self._vu_l.show(); self._vu_r.show()

    def resizeEvent(self, ev):
        if not self._compact:
            self._vu_r.setGeometry(self.width() - 94, 12, 84, 84)
            self._vu_l.setGeometry(self.width() - 184, 12, 84, 84)

    # --- pittura -------------------------------------------------------------
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        # ghiera esterna metallica
        g_frame = QLinearGradient(0, 0, 0, h)
        g_frame.setColorAt(0.0, QColor("#4a4e56"))
        g_frame.setColorAt(0.5, QColor("#2c2f36"))
        g_frame.setColorAt(1.0, QColor("#17181d"))
        p.setPen(QPen(QColor(0, 0, 0, 190), 1))
        p.setBrush(g_frame)
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 7, 7)

        # schermo incassato
        scr = QRectF(6, 6, w - 12, h - 12)
        g_scr = QRadialGradient(QPointF(scr.center().x(), scr.top()), h * 1.6)
        g_scr.setColorAt(0.0, QColor("#171208"))
        g_scr.setColorAt(1.0, QColor(theme.LCD_BG))
        p.setPen(QPen(QColor(0, 0, 0, 230), 2))
        p.setBrush(g_scr)
        p.drawRoundedRect(scr, 6, 6)

        # scanline LCD
        p.setPen(QPen(QColor(255, 255, 255, 8), 1))
        y = int(scr.top()) + 2
        while y < scr.bottom() - 2:
            p.drawLine(int(scr.left() + 3), y, int(scr.right() - 3), y)
            y += 3

        # vitette sulla ghiera
        theme.draw_screws(p, self.rect().adjusted(2, 2, -2, -2), inset=6)

        # --- contenuto -----------------------------------------------------
        big = 30 if not self._compact else 22
        tx = scr.left() + 18

        # tempo grande con bagliore
        p.setFont(_mono_font(big, bold=True))
        t = f"{Player_fmt(self._pos)} / {Player_fmt(self._dur)}"
        _glow_text(p, QRectF(tx, scr.top() + 6, 260, big + 10),
                   t, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # titolo brano (eliso)
        p.setFont(_ui_font(14, bold=True))
        fm = p.fontMetrics()
        max_w = w - 320 if not self._compact else w - 36
        title = fm.elidedText(self._track, Qt.TextElideMode.ElideRight, int(max_w))
        _glow_text(p, QRectF(tx, scr.top() + (52 if not self._compact else 40),
                             max_w, 22 if not self._compact else 16), title,
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   color=QColor("#f4e3bd"))

        # stato (LED + testo)
        led_y = scr.top() + (82 if not self._compact else 58)
        col_map = {"play": "#67e26b", "pause": "#ffc93c", "stop": "#8a8f96",
                   "end": "#f2801e"}
        led_c = QColor(col_map.get(self._state_kind, "#8a8f96"))
        g_led = QRadialGradient(QPointF(tx + 6, led_y + 7), 8)
        g_led.setColorAt(0.0, led_c.lighter(150))
        g_led.setColorAt(1.0, led_c.darker(160))
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.setBrush(g_led)
        p.drawEllipse(QPointF(tx + 6, led_y + 7), 4.4, 4.4)
        p.setFont(_ui_font(12, bold=True, spacing=1.2))
        p.setPen(QPen(QColor("#d9cfb6")))
        p.drawText(QRectF(tx + 16, led_y - 2, 240, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self._state_text)

        # badge destra (rate / shuffle / repeat / mute)
        badges = [(f"{self._rate:.2f}×", True, theme.LCD_GLOW)]
        if self._shuffle:
            badges.append(("S", True, theme.LCD_GLOW))
        if self._repeat == "all":
            badges.append(("R", True, theme.LCD_GLOW))
        elif self._repeat == "one":
            badges.append(("R1", True, theme.LCD_GLOW))
        if self._muted:
            badges.append(("MUTE", True, QColor("#ff8f6b")))
        if self._hint:
            badges.append((self._hint, True, QColor("#9fd0ff")))

        p.setFont(_mono_font(11, bold=True))
        bx = w - 26
        by = scr.bottom() - 24
        for text, _lit, col in reversed(badges):
            tw = p.fontMetrics().horizontalAdvance(text) + 14
            rect = QRectF(bx - tw, by, tw, 20)
            p.setPen(QPen(QColor(0, 0, 0, 160), 1))
            p.setBrush(QColor(255, 255, 255, 10))
            p.drawRoundedRect(rect, 4, 4)
            p.setPen(QPen(col))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            bx -= tw + 8
        p.end()


def Player_fmt(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _glow_text(p, rect, text, flags, color=None):
    """Testo con bagliore ambra (effetto LCD)."""
    col = color or QColor(theme.LCD_GLOW)
    p.setPen(QColor(col.red(), col.green(), col.blue(), 36))
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0)):
        p.drawText(rect.translated(dx, dy), flags, text)
    p.setPen(col)
    p.drawText(rect, flags, text)


# ---------------------------------------------------------------------------
# Righe di contorno riutilizzabili
# ---------------------------------------------------------------------------
class EtchedLabel(QLabel):
    """Testo inciso sul metallo (intestazioni)."""

    def __init__(self, text, px=12, spacing=2.0, color=theme.PANEL_DIM):
        super().__init__(text)
        f = QFont()
        f.setFamilies(theme.FONT_UI)
        f.setPixelSize(px)
        f.setBold(True)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        self.setFont(f)
        self.setStyleSheet(f"color: {color}; background: transparent;")
