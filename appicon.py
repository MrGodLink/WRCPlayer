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
from PySide6.QtGui import (QColor, QConicalGradient, QIcon, QImage, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)

# Disegno normalizzato su una tela 256x256.
_D = 256.0


def paint_orb(painter, rect):
    """Disegna l'icona (sfera di play) dentro `rect`, mantenendo il quadrato."""
    p = painter
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    side = min(rect.width(), rect.height())
    x = rect.x() + (rect.width() - side) / 2.0
    y = rect.y() + (rect.height() - side) / 2.0
    s = side / _D  # fattore di scala dal disegno normalizzato

    # --- proiezione/ombra a terra -----------------------------------------
    sh = QRadialGradient(QPointF(x + 128 * s, y + 246 * s), 88 * s)
    sh.setColorAt(0.0, QColor(0, 0, 0, 110))
    sh.setColorAt(0.7, QColor(0, 0, 0, 40))
    sh.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(sh)
    p.drawEllipse(QRectF(x + 48 * s, y + 214 * s, 160 * s, 44 * s))

    # --- ghiera metallica esterna (gradiente conico argento) ---------------
    ring = QRectF(x + 20 * s, y + 16 * s, 216 * s, 216 * s)
    g_ring = QConicalGradient(ring.center(), 30)
    for stop, col in ((0.00, "#f0f2f5"), (0.18, "#82878f"),
                      (0.32, "#e6e8ec"), (0.50, "#5d626a"),
                      (0.68, "#cfd3d9"), (0.82, "#6a6f77"),
                      (1.00, "#f0f2f5")):
        g_ring.setColorAt(stop, QColor(col))
    p.setBrush(g_ring)
    p.setPen(QPen(QColor(10, 12, 16, 200), 1.6 * s))
    p.drawEllipse(ring)

    # --- faccia interna -----------------------------------------------------
    face = QRectF(x + 38 * s, y + 34 * s, 180 * s, 180 * s)
    g_face = QRadialGradient(QPointF(face.center().x(), face.top() + 40 * s),
                             120 * s)
    g_face.setColorAt(0.0, QColor("#7d9bf2"))
    g_face.setColorAt(0.45, QColor("#3f57c8"))
    g_face.setColorAt(0.80, QColor("#221f77"))
    g_face.setColorAt(1.0, QColor("#120f3e"))
    p.setBrush(g_face)
    p.setPen(QPen(QColor(0, 0, 0, 140), 1.2 * s))
    p.drawEllipse(face)

    # riflesso interno in basso (luce rimbalzata)
    g_bot = QRadialGradient(QPointF(face.center().x(), face.bottom() - 20 * s),
                            70 * s)
    g_bot.setColorAt(0.0, QColor(255, 138, 60, 70))
    g_bot.setColorAt(1.0, QColor(255, 138, 60, 0))
    p.setBrush(g_bot)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(face.adjusted(4 * s, 4 * s, -4 * s, -4 * s))

    # --- riflesso lucido superiore ------------------------------------------
    gloss = QPainterPath()
    gloss.moveTo(face.left() + 8 * s, face.center().y() + 6 * s)
    gloss.quadTo(face.center().x(), face.top() + 4 * s,
                 face.right() - 8 * s, face.center().y() + 6 * s)
    gloss.quadTo(face.center().x(), face.top() + 52 * s,
                 face.left() + 8 * s, face.center().y() + 6 * s)
    gloss.closeSubpath()
    p.fillPath(gloss, QColor(255, 255, 255, 52))

    # --- glifo di play bianco inciso ----------------------------------------
    tri = QPainterPath()
    cx, cy = face.center().x(), face.center().y()
    tri.moveTo(cx - 26 * s, cy - 44 * s)
    tri.lineTo(cx + 44 * s, cy)
    tri.lineTo(cx - 26 * s, cy + 44 * s)
    tri.closeSubpath()

    p.setPen(QPen(QColor(255, 255, 255, 60), 1.4 * s))
    p.setBrush(QColor(255, 255, 255, 34))
    p.drawPath(tri.translated(QPointF(0, 2.6 * s)))  # ombra incisa

    g_tri = QRadialGradient(QPointF(cx - 6 * s, cy - 10 * s), 70 * s)
    g_tri.setColorAt(0.0, QColor("#ffffff"))
    g_tri.setColorAt(1.0, QColor("#c9d4ee"))
    p.setBrush(g_tri)
    p.setPen(QPen(QColor(255, 255, 255, 170), 1.0 * s))
    p.drawPath(tri)

    # puntino arancio "LED" sul bordo della ghiera (richiamo al tema)
    led = QRectF(x + 206 * s, y + 44 * s, 14 * s, 14 * s)
    g_led = QRadialGradient(QPointF(led.center().x() - 2 * s,
                                    led.center().y() - 2 * s), 9 * s)
    g_led.setColorAt(0.0, QColor("#ffd9a0"))
    g_led.setColorAt(0.45, QColor("#f2801e"))
    g_led.setColorAt(1.0, QColor("#7a3a00"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(g_led)
    p.drawEllipse(led)

    p.restore()


def create_app_icon(size=256):
    """QIcon generato a runtime (nessun file esterno necessario)."""
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    paint_orb(p, QRectF(0, 0, size, size))
    p.end()
    return QIcon(QPixmap.fromImage(img))


def make_asset_files(png_dir, ico_path=None, sizes=(16, 24, 32, 48, 64, 128, 256)):
    """Esporta i PNG nelle varie dimensioni (+ .ico se e' disponibile PIL)."""
    import os
    os.makedirs(png_dir, exist_ok=True)
    paths = []
    for s in sizes:
        img = QImage(s, s, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        paint_orb(p, QRectF(0, 0, s, s))
        p.end()
        fp = os.path.join(png_dir, f"icon_{s}.png")
        img.save(fp)
        paths.append(fp)

    if ico_path:
        try:
            from PIL import Image
            by_size = {}
            for fp in paths:
                s = int(os.path.basename(fp)[6:-4])
                by_size[s] = fp
            order = sorted(by_size)
            base = Image.open(by_size[order[-1]]).convert("RGBA")
            small = [Image.open(by_size[s]).convert("RGBA")
                     for s in order[:-1]]
            base.save(ico_path, format="ICO", append_images=small)
            paths.append(ico_path)
        except Exception as e:  # PIL assente: si stanno bene i soli PNG
            print("ICO non generato:", e)
    return paths
