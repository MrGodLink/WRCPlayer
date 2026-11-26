# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Raffaele Catapano (MrGodLink)
# Renders docs/*.png with the demo engine (no media files needed).
"""Genera le schermate del README: `python scripts/make_screenshots.py`."""
import os
import sys
import tempfile

os.environ["WRC_MOCK"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import theme  # noqa: E402
from player import PlayerWindow  # noqa: E402


def main():
    app = QApplication(sys.argv)
    theme.apply_app_qss(app)
    tmp = tempfile.mkdtemp()
    names = ["Summer_Demo_Track.mp3", "Demo_02_funky_beat.flac",
             "Demo_03_late_night_jazz.mp3", "Vacanze_2026_clip.mp4"]
    for n in names:
        open(os.path.join(tmp, n), "w").close()
    p = [os.path.join(tmp, n) for n in names]
    w = PlayerWindow()
    w.show()
    for x in p:
        w.playlist.add_path(x)
    out = os.path.join(ROOT, "docs")
    os.makedirs(out, exist_ok=True)

    def shot(name):
        w.grab().save(os.path.join(out, name))

    steps = [
        lambda: w.play_path(p[0]),
        lambda: shot("preview_audio.png"),
        lambda: (w.toggle_playlist(), w.btn_playlist.setChecked(True)),
        lambda: shot("preview_playlist.png"),
        lambda: (w.toggle_playlist(), w.play_path(p[3])),
        lambda: shot("preview_video.png"),
        app.quit,
    ]
    for i, f in enumerate(steps):
        QTimer.singleShot(700 * (i + 1), f)
    app.exec()


if __name__ == "__main__":
    main()
