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

"""Motore fittizio per demo e sviluppo (usato quando WMP COM e Qt Multimedia
non sono disponibili, oppure forzato con WRC_MOCK=1).

Simula la riproduzione con un cronometro e disegna una "trasmittente" di
prova nel pannello video, cosi' l'interfaccia resta pienamente provabile
anche fuori da Windows.
"""

import os

from PySide6.QtCore import QElapsedTimer, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

PS_STOPPED, PS_PAUSED, PS_PLAYING, PS_MEDIAENDED = 1, 2, 3, 8

_BARS = ["#ffffff", "#f0d020", "#20e0e0", "#20e040", "#e040e0", "#e02020",
         "#2040e0", "#101010"]


class FakeVideoWidget(QWidget):
    """Trasmittente di prova SMPTE-ish animata (solo per la demo)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = QElapsedTimer()
        self._t.start()
        self.setMinimumSize(320, 200)
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(40)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#000000"))

        band_h = h * 0.68
        bw = w / len(_BARS)
        for i, col in enumerate(_BARS):
            p.fillRect(QRectF(i * bw, 0, bw + 1, band_h), QColor(col))

        # riga inferiore agradiente + cerchio rotante (movimento)
        g = QLinearGradient(0, band_h, w, h)
        g.setColorAt(0.0, QColor("#1b1f27"))
        g.setColorAt(1.0, QColor("#0a0c10"))
        p.fillRect(QRectF(0, band_h, w, h - band_h), g)
        import math
        t = self._t.elapsed() / 1000.0
        ang = t * 1.6
        cx = w * 0.5 + math.cos(ang) * w * 0.22
        cy = band_h + (h - band_h) * 0.55
        g2 = QRadialGradient(cx, cy, 26)
        g2.setColorAt(0.0, QColor("#ffd9a0"))
        g2.setColorAt(1.0, QColor("#b85c00"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g2)
        p.drawEllipse(QRectF(cx - 18, cy - 18, 36, 36))

        f = QFont()
        f.setFamilies(["Consolas", "DejaVu Sans Mono", "monospace"])
        f.setPixelSize(max(12, int(h * 0.075)))
        f.setBold(True)
        p.setFont(f)
        p.setPen(QPen(QColor(0, 0, 0, 180), 2))
        p.drawText(QRectF(0, 0, w, band_h),
                   Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                   "TRASMITTENTE DI PROVA (motore demo)")
        p.end()


class MockEngine:
    engine_name = "Mock « "
    supports_video = True

    def __init__(self):
        self._timer = QElapsedTimer()
        self._timer.start()
        self._path = None
        self._duration = 184.0
        self._pos0 = 0.0
        self._state = PS_STOPPED
        self._volume = 100
        self._mute = False
        self._rate = 1.0
        self._video = FakeVideoWidget()
        # tick "virtuale": lo stato avanza consultando il cronometro
        self._tick = QTimer()
        self._tick.setInterval(200)
        self._tick.timeout.connect(self._check_end)
        self._tick.start()

    @property
    def version(self):
        return "demo 1.0"

    @property
    def widget(self):
        return self._video

    def _check_end(self):
        if self._state == PS_PLAYING and self.position >= self._duration:
            self._state = PS_MEDIAENDED

    def load(self, path):
        self._path = path
        ext = os.path.splitext(path)[1].lower()
        self._duration = 152.0 if ext in (".mp4", ".mkv", ".avi", ".wmv",
                                          ".mov", ".m4v") else 184.0
        self._pos0 = 0.0
        self._timer.restart()
        self._state = PS_PLAYING

    def play(self):
        if self._state == PS_PAUSED:
            self._pos0 = self.position
        self._timer.restart()
        self._state = PS_PLAYING

    def pause(self):
        if self._state == PS_PLAYING:
            self._pos0 = self.position
            self._state = PS_PAUSED

    def stop(self):
        self._state = PS_STOPPED
        self._pos0 = 0.0
        self._timer.restart()

    @property
    def play_state(self):
        return self._state

    @property
    def duration(self):
        return self._duration

    @property
    def position(self):
        if self._state == PS_PLAYING:
            return min(self._duration,
                       self._pos0 + self._timer.elapsed() / 1000.0 * self._rate)
        return self._pos0

    @position.setter
    def position(self, seconds):
        self._pos0 = max(0.0, min(self._duration, float(seconds)))
        self._timer.restart()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, v):
        self._volume = int(v)

    @property
    def mute(self):
        return self._mute

    @mute.setter
    def mute(self, v):
        self._mute = bool(v)

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, v):
        self._rate = float(v)
