# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Raffaele Catapano (MrGodLink)
# Exports assets/app_icon.ico and assets/icons/*.png from appicon.py.
"""Genera le icone per la confezione: `python scripts/make_assets.py`
(richiede Pillow per l'.ico: pip install pillow)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtGui import QGuiApplication  # noqa: E402

from appicon import make_asset_files  # noqa: E402

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    out = os.path.join(ROOT, "assets")
    files = make_asset_files(os.path.join(out, "icons"),
                             os.path.join(out, "app_icon.ico"))
    print("\n".join(files))
