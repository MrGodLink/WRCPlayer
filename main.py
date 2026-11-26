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

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import theme
from appicon import create_app_icon
from player import PlayerWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("WRCPlayer")

    icon = create_app_icon(256)
    app.setWindowIcon(icon)

    theme.apply_app_qss(app)

    win = PlayerWindow()
    win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
