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

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout,
                               QWidget)

import theme

MEDIA_FILTER = ("Audio e video (*.mp3 *.aac *.m4a *.wma *.wav *.flac *.ogg "
                "*.opus *.mp4 *.m4v *.mkv *.avi *.wmv *.mov *.mpg *.mpeg "
                "*.webm *.ts *.3gp);;Tutti i file (*)")


class PlaylistWidget(QWidget):
    pathActivated = Signal(str)
    pathsAdded = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        self.setStyleSheet(
            "PlaylistWidget { background: rgba(12,13,16,0.97); "
            "border: 1px solid rgba(0,0,0,0.75); "
            "border-top: 1px solid rgba(255,255,255,0.10); }")

        head = QHBoxLayout()
        lbl = QLabel_head("SCALETTA")
        head.addWidget(lbl)
        head.addStretch()
        layout.addLayout(head)

        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0c0d11, stop:1 #14161b);
                color: #d8d3c8; font-size: 13px;
                border: 1px solid rgba(0,0,0,0.7);
                border-top: 1px solid rgba(255,255,255,0.06);
                outline: none; alternate-background-color: #12141a;
            }
            QListWidget::item { padding: 6px 12px; min-height: 22px;
                border-bottom: 1px solid rgba(255,255,255,0.03); }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(242,128,30,0.90), stop:1 rgba(184,92,0,0.90));
                color: #ffffff; }
            QListWidget::item:hover:!selected {
                background: rgba(255,255,255,0.06); }
        """)
        self.list.setAlternatingRowColors(True)
        self.list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list)

        row = QHBoxLayout()
        self.btn_load = QPushButton("Carica M3U…")
        self.btn_save = QPushButton("Salva M3U…")
        self.btn_remove = QPushButton("Rimuovi")
        self.btn_clear = QPushButton("Svuota")
        for b in (self.btn_load, self.btn_save, self.btn_remove, self.btn_clear):
            b.setStyleSheet(theme.METAL_BUTTON_QSS)
            row.addWidget(b)
        row.addStretch()
        layout.addLayout(row)

        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_clear.clicked.connect(self.list.clear)
        self.btn_save.clicked.connect(self.save_m3u)
        self.btn_load.clicked.connect(self.load_m3u)

    # --- eventi -------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        added = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                p = url.toLocalFile()
                self.add_path(p)
                added.append(p)
        if added:
            self.pathsAdded.emit(added)

    # --- azioni -------------------------------------------------------------
    def _on_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.pathActivated.emit(path)

    def _remove_selected(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))

    def save_m3u(self):
        paths = self.paths()
        if not paths:
            return
        fp, _ = QFileDialog.getSaveFileName(self, "Salva scaletta",
                                            "scaletta.m3u",
                                            "Playlist M3U (*.m3u)")
        if not fp:
            return
        if not fp.lower().endswith(".m3u"):
            fp += ".m3u"
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for p in paths:
                    f.write(p.replace("\\", "/") + "\n")
        except OSError:
            pass

    def load_m3u(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Carica scaletta", "",
                                            "Playlist M3U (*.m3u);;" + MEDIA_FILTER)
        if not fp:
            return
        added = []
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if os.path.isfile(line):
                        self.add_path(line)
                        added.append(line)
                    elif os.path.isfile(os.path.join(os.path.dirname(fp), line)):
                        p = os.path.join(os.path.dirname(fp), line)
                        self.add_path(p)
                        added.append(p)
        except OSError:
            pass
        if added:
            self.pathsAdded.emit(added)

    # --- API ---------------------------------------------------------------
    def add_paths(self, paths):
        for p in paths:
            self.add_path(p)

    def add_path(self, path):
        if path in self.paths():
            return
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setToolTip(path)
        self.list.addItem(item)

    def paths(self):
        return [self.list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.list.count())]

    def set_current(self, path):
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == path:
                self.list.setCurrentRow(i)
                break


def QLabel_head(text):
    """Intestazione incisa con vite decorativa."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    f = QFont()
    f.setFamilies(theme.FONT_UI)
    f.setPixelSize(12)
    f.setBold(True)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.5)
    lbl.setFont(f)
    lbl.setStyleSheet(
        "color: #b98a4e; background: transparent; padding-left: 2px;")
    return lbl
