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
import random
import time

from PySide6.QtCore import QEvent, QSettings, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                               QStackedLayout, QVBoxLayout, QWidget)

from controls import (BrushedPanel, EtchedLabel, LcdDisplay, MetalButton,
                      MetalSlider, FOLDER, FULLSCREEN, LIST, MINUS, MONITOR,
                      NEXT, OPEN_FILE, PAUSE, PIN, PLAY, PLUS, PREV,
                      REPEAT, REPEAT_ONE, SHUFFLE, SPEAKER, SPEAKER_MUTE,
                      STOP)
from wmp_engine import (PS_MEDIAENDED, PS_PAUSED, PS_PLAYING, PS_STOPPED,
                        WmpEngine)
from playlist import MEDIA_FILTER, PlaylistWidget

AUDIO_EXTS = {".mp3", ".aac", ".m4a", ".m4b", ".wma", ".wav", ".flac", ".ogg",
              ".oga", ".opus", ".mid", ".midi", ".cda", ".aiff", ".ape",
              ".mka"}
VIDEO_EXTS = {".mp4", ".m4v", ".mkv", ".avi", ".wmv", ".mov", ".mpg",
              ".mpeg", ".mpe", ".webm", ".ts", ".m2ts", ".3gp", ".3g2",
              ".vob", ".flv", ".ogv", ".divx"}

# Formati che WMP Legacy sa decodificare; il resto (ogg/opus/ape/mka...)
# va direttamente a Qt/FFmpeg invece di fallire in WMP.
WMP_AUDIO_EXTS = {".mp3", ".aac", ".m4a", ".m4b", ".wma", ".wav", ".flac",
                  ".mid", ".midi", ".cda", ".aiff"}

MEDIA_FILTER_ALL = ("Tutti i media (*.mp3 *.aac *.m4a *.wma *.wav *.flac "
                    "*.ogg *.opus *.mp4 *.m4v *.mkv *.avi *.wmv *.mov "
                    "*.mpg *.mpeg *.webm *.ts *.3gp);;Tutti i file (*)")

RATE_STEPS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

STATE_TEXT = {PS_PLAYING: "Riproduzione in corso", PS_PAUSED: "Pausa",
              PS_STOPPED: "Fermo", PS_MEDIAENDED: "Fine brano"}
STATE_KIND = {PS_PLAYING: "play", PS_PAUSED: "pause", PS_STOPPED: "stop",
              PS_MEDIAENDED: "end"}

AUDIO_SIZE = (620, 336)
VIDEO_SIZE = (980, 660)


def classify(path):
    return "video" if os.path.splitext(path)[1].lower() in VIDEO_EXTS \
        else "audio"


def _media_files(folder):
    ok = AUDIO_EXTS | VIDEO_EXTS
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    return [os.path.join(folder, n) for n in names
            if os.path.splitext(n)[1].lower() in ok]


class PlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(520, 300)
        self.setStyleSheet("background-color: #101114;")

        self._current_path = None
        self._seeking = False
        self._ended_handled = False
        self._muted = False
        self._rate_idx = 2
        self._shuffle = False
        self._repeat = "off"
        self._on_top = False
        self._mode = "audio"
        self._panel_visible = False
        self._video_forced = None      # None = automatico, True/False = forzato
        self._video_widget = None
        self._vu_l = 0.0
        self._vu_r = 0.0
        self._fs_active = False
        self._fs_was_max = False
        self._fs_last_pos = None
        self._fs_idle = 0.0
        self._fs_pl = False
        self._video_qss = ""
        self._fallback_tried = False
        self._engine_notice = None
        self.store = QSettings("MrGodLink", "WRCPlayer")

        self._build_engines()
        self._build_ui()
        # Se il motore attuale gestisce gia' il video (mock o Qt usato
        # anche per l'audio), collega subito il suo widget al pannello.
        # (prima si controllava solo _eng_video: con Qt come unico motore,
        # cioe' senza WMP, il widget video non veniva mai collegato)
        if self.engine.supports_video:
            self._set_video_widget(self.engine.widget)
        self._connect()
        self._shortcuts()
        self._restore_settings()

        eng = self._eng_audio
        title = "WRCPlayer"
        if eng is not None:
            title += f" » {eng.engine_name}"
            # v = getattr(eng, "version", None)
            # if v:
            #    title += f"  ({v})"
        self._base_title = title
        self.setWindowTitle(title)

        # Avvio in stile minimal: solo display audio, nessun pannello video.
        self._apply_mode("audio", initial=True)
        if self._engine_notice:
            self.lcd.set_hint(self._engine_notice)

        # Il loop eventi Qt pompa i messaggi Windows: WMP transita di stato.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(120)

    # ------------------------------------------------------------------ motori
    def _build_engines(self):
        """Sceglie i motori: WMP COM per l'audio, Qt per il video, mock come
        ultimo recurso (anche forzando WRC_MOCK=1)."""
        self._eng_audio = None
        self._eng_video = None
        self._engine_notice = None
        if os.environ.get("WRC_MOCK") == "1":
            from mock_engine import MockEngine
            self._eng_audio = MockEngine()
            self._eng_video = self._eng_audio
        else:
            # WRC_ENGINE=qt salta WMP e usa solo Qt Multimedia
            if os.environ.get("WRC_ENGINE", "").lower() != "qt":
                try:
                    self._eng_audio = WmpEngine()
                except Exception as e:
                    print("Motore WMP non disponibile:", e)
                    self._engine_notice = "WMP assente: motore Qt"
            try:
                from qt_engine import QtMediaEngine
                qt = QtMediaEngine()
                if self._eng_audio is None:
                    self._eng_audio = qt   # Qt riproduce anche l'audio
                else:
                    self._eng_video = qt
            except Exception as e:
                print("Motore video Qt non disponibile:", e)
            if self._eng_audio is None:
                from mock_engine import MockEngine
                self._eng_audio = MockEngine()
                self._eng_video = self._eng_audio
        self.engine = self._eng_audio
        self._sync_engine_settings()

    def engine_for(self, kind):
        if kind == "video" and self._eng_video is not None:
            return self._eng_video
        return self._eng_audio

    def _pick_engine(self, path):
        qt = self._eng_video
        if classify(path) == "video":
            return qt or self._eng_audio
        ext = os.path.splitext(path)[1].lower()
        if qt is not None and qt is not self._eng_audio \
                and ext not in WMP_AUDIO_EXTS:
            return qt
        return self._eng_audio

    def _retry_with_qt(self):
        """WMP non riesce a decodificare il file: ritenta con Qt (una volta)."""
        qt = self._eng_video
        if self._fallback_tried or qt is None or qt is self.engine \
                or not self._current_path:
            return
        self._fallback_tried = True
        self._switch_engine(qt)
        self.engine.load(os.path.normpath(self._current_path))
        self.lcd.set_hint("motore Qt")

    def _switch_engine(self, new):
        if new is self.engine:
            return
        try:
            self.engine.stop()
        except Exception:
            pass
        self.engine = new
        self._sync_engine_settings()
        self._set_video_widget(new.widget if new.supports_video else None)

    def _sync_engine_settings(self):
        e = self.engine
        try:
            e.volume = self.volume.value() if hasattr(self, "volume") else 100
        except Exception:
            pass
        try:
            e.mute = self._muted
        except Exception:
            pass
        try:
            e.rate = RATE_STEPS[self._rate_idx]
        except Exception:
            pass

    # ---------------------------------------------------------------------- UI
    def _build_ui(self):
        central = BrushedPanel()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # pannello video (visibile solo per i file video)
        self.video_panel = QWidget()
        self.video_panel.setObjectName("videoPanel")
        self.video_panel.setStyleSheet("""
            #videoPanel { background-color: #06070a;
                          border: 1px solid rgba(0,0,0,0.8);
                          border-top: 1px solid rgba(255,255,255,0.07); }
        """)
        self.video_stack = QStackedLayout(self.video_panel)
        self.video_stack.setContentsMargins(1, 1, 1, 1)
        self.video_placeholder = QLabel(
            "Pannello video\n\nApri un file video (mp4, mkv, avi, wmv…) "
            "per attivarlo;\ni file musicali restano in stile minimal, "
            "senza zona video.")
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_placeholder.setWordWrap(True)
        self.video_placeholder.setStyleSheet(
            "color: #6f747c; background: transparent; font-size: 14px;")
        self.video_stack.addWidget(self.video_placeholder)
        root.addWidget(self.video_panel, 1)

        # display LCD/VFD
        self.lcd = LcdDisplay()
        root.addWidget(self.lcd)

        # barra comandi
        self.bar_widget = QWidget()
        self.bar_widget.setObjectName("barBox")
        self.bar_widget.setStyleSheet("#barBox { background: transparent; }")
        bar = QVBoxLayout(self.bar_widget)
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(6)

        self.util_widget = QWidget()
        self.util_widget.setObjectName("utilBox")
        self.util_widget.setStyleSheet("#utilBox { background: transparent; }")
        util = QHBoxLayout(self.util_widget)
        util.setContentsMargins(0, 0, 0, 0)
        util.setSpacing(5)
        self.app_label = EtchedLabel(" « WRC Player » [ Raffaele Catapano ]", 11, 2.5)
        util.addWidget(self.app_label)
        util.addStretch()
        small = 30
        self.btn_open = MetalButton(OPEN_FILE, small,
                                    tooltip="Apri file (Ctrl+O)")
        self.btn_folder = MetalButton(FOLDER, small,
                                      tooltip="Apri cartella (Ctrl+Shift+O)")
        self.btn_playlist = MetalButton(LIST, small, checkable=True,
                                        tooltip="Scaletta (L)")
        self.btn_monitor = MetalButton(MONITOR, small, checkable=True,
                                       tooltip="Mostra/nascondi pannello video (V)")
        self.btn_full = MetalButton(FULLSCREEN, small,
                                    tooltip="Schermo intero (F)")
        self.btn_pin = MetalButton(PIN, small, checkable=True,
                                   tooltip="Sempre in primo piano (T)")
        for b in (self.btn_open, self.btn_folder, self.btn_playlist,
                  self.btn_monitor, self.btn_full, self.btn_pin):
            util.addWidget(b)
        bar.addWidget(self.util_widget)

        self.progress = MetalSlider()
        bar.addWidget(self.progress)

        row = QHBoxLayout()
        row.setSpacing(5)
        self.btn_prev = MetalButton(PREV, 44, tooltip="Brano precedente (P)")
        self.btn_play = MetalButton(PLAY, 52, tooltip="Riproduci/Pausa (Spazio)")
        self.btn_stop = MetalButton(STOP, 44, tooltip="Ferma")
        self.btn_next = MetalButton(NEXT, 44, tooltip="Brano successivo (N)")
        for b in (self.btn_prev, self.btn_play, self.btn_stop, self.btn_next):
            row.addWidget(b)

        row.addSpacing(12)
        self.btn_mute = MetalButton(SPEAKER, 38, checkable=True,
                                    tooltip="Muto (M)")
        row.addWidget(self.btn_mute)
        self.volume = MetalSlider()
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setFixedWidth(110)
        row.addWidget(self.volume)

        row.addSpacing(12)
        self.btn_rate_down = MetalButton(MINUS, 30, tooltip="Velocità −")
        self.rate_label = QLabel("1.00×")
        self.rate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rate_label.setFixedWidth(54)
        self.rate_label.setStyleSheet("""
            QLabel { background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #0c0d11, stop:1 #14161b);
                     color: #ffcf80; font-family: "Consolas";
                     font-size: 12px; font-weight: bold;
                     border: 1px solid rgba(0,0,0,0.7);
                     border-top: 1px solid rgba(255,255,255,0.08);
                     border-radius: 4px; }
        """)
        self.btn_rate_up = MetalButton(PLUS, 30, tooltip="Velocità +")
        row.addWidget(self.btn_rate_down)
        row.addWidget(self.rate_label)
        row.addWidget(self.btn_rate_up)

        row.addSpacing(10)
        self.btn_shuffle = MetalButton(SHUFFLE, 30, checkable=True,
                                       tooltip="Riproduzione casuale (S)")
        self.btn_repeat = MetalButton(REPEAT, 30, checkable=True,
                                      tooltip="Ripetizione: no → tutto → brano (R)")
        row.addWidget(self.btn_shuffle)
        row.addWidget(self.btn_repeat)

        row.addStretch()
        bar.addLayout(row)
        root.addWidget(self.bar_widget)

        # scaletta (nascosta all'avvio: finestra minimal)
        self.playlist = PlaylistWidget()
        self.playlist.setMaximumHeight(220)
        self.playlist.hide()
        root.addWidget(self.playlist)

    def _connect(self):
        self.btn_play.clicked.connect(self.toggle_play)
        # lambda: self.engine cambia a runtime (prima il bound method restava
        # agganciato al motore iniziale e Stop non fermava il video)
        self.btn_stop.clicked.connect(lambda: self.engine.stop())
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_open.clicked.connect(self.open_file)
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_playlist.clicked.connect(self.toggle_playlist)
        self.btn_monitor.clicked.connect(self.toggle_video_panel)
        self.btn_full.clicked.connect(self.toggle_fullscreen)
        self.btn_pin.clicked.connect(self.toggle_on_top)
        self.btn_mute.clicked.connect(self.toggle_mute)
        self.btn_rate_down.clicked.connect(lambda: self._set_speed(
            self._rate_idx - 1))
        self.btn_rate_up.clicked.connect(lambda: self._set_speed(
            self._rate_idx + 1))
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat.clicked.connect(self.cycle_repeat)

        self.volume.valueChanged.connect(self._set_volume)
        self.progress.sliderPressed.connect(lambda: setattr(self, "_seeking",
                                                            True))
        self.progress.sliderReleased.connect(self._seek_release)
        self.progress.sliderMoved.connect(self._seek_preview)

        self.playlist.pathActivated.connect(self.play_path)
        self.playlist.pathsAdded.connect(self._on_paths_added)

    def _shortcuts(self):
        mapping = {
            "Space": self.toggle_play,
            "Ctrl+O": self.open_file,
            "Ctrl+Shift+O": self.open_folder,
            "Right": lambda: self.seek_relative(5),
            "Left": lambda: self.seek_relative(-5),
            "Shift+Right": lambda: self.seek_relative(30),
            "Shift+Left": lambda: self.seek_relative(-30),
            "Up": lambda: self.volume_relative(5),
            "Down": lambda: self.volume_relative(-5),
            "M": self.toggle_mute,
            "N": self.next_track,
            "P": self.prev_track,
            "S": self.toggle_shuffle,
            "R": self.cycle_repeat,
            "F": self.toggle_fullscreen,
            "T": self.toggle_on_top,
            "L": self.toggle_playlist,
            "V": self.toggle_video_panel,
            "[": lambda: self._set_speed(self._rate_idx - 1),
            "]": lambda: self._set_speed(self._rate_idx + 1),
            "Esc": self._escape,
        }
        for key, fn in mapping.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(fn)

    # ------------------------------------------------------------------ modi
    def _apply_mode(self, kind, initial=False):
        """Audio => finestra minimal senza pannello video;
        Video => pannello video visibile e finestra piu' grande."""
        self._mode = kind
        want_panel = (kind == "video" and self._video_widget is not None)
        if self._video_forced is not None:
            want_panel = bool(self._video_forced) and \
                self._video_widget is not None

        if self.isFullScreen() and not want_panel:
            self._leave_fullscreen()   # brano audio a schermo intero: esci

        if not want_panel and self.isMaximized():       # NUOVO
            self.showNormal()          # modalità minima: mai massimizzata
        self._set_maximizable(want_panel)               # NUOVO
        self.btn_full.setVisible(want_panel)            # NUOVO

        self.lcd.set_compact(want_panel)
        self.video_panel.setVisible(want_panel)
        self.btn_monitor.setChecked(want_panel)
        if want_panel and self._video_widget is not None:
            self.video_stack.setCurrentWidget(self._video_widget)

        if initial or want_panel != self._panel_visible:
            self._resize_for(want_panel)
        self._panel_visible = want_panel

    def _set_maximizable(self, on):
        hint = Qt.WindowType.WindowMaximizeButtonHint
        if bool(self.windowFlags() & hint) == on:
            return
        self.setWindowFlag(hint, on)
        if self.isVisible():
            self.show()   # setWindowFlag nasconde la finestra

    def _resize_for(self, panel):
        if self.isFullScreen():
            return
        scr = self.screen() or QGuiApplication.primaryScreen()
        avail = scr.availableGeometry() if scr else None
        w, h = VIDEO_SIZE if panel else AUDIO_SIZE
        if self.playlist.isVisible():
            h += min(220, self.playlist.sizeHint().height() or 180)
        if avail is not None:
            w = min(w, avail.width() - 60)
            h = min(h, avail.height() - 80)
        self.resize(w, h)

    def _set_video_widget(self, w):
        if w is self._video_widget:
            return
        if self._video_widget is not None:
            try:
                self._video_widget.removeEventFilter(self)
            except Exception:
                pass
            self.video_stack.removeWidget(self._video_widget)
        self._video_widget = w
        if w is not None:
            self.video_stack.addWidget(w)
            w.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self._video_widget and \
                ev.type() == QEvent.Type.MouseButtonDblClick:
            self.toggle_fullscreen()
            return True
        return super().eventFilter(obj, ev)

    # ------------------------------------------------------------ riproduzione
    def toggle_play(self):
        if self.engine.play_state == PS_PLAYING:
            self.engine.pause()
        else:
            self.engine.play()

    def play_path(self, path):
        if not os.path.isfile(path):
            self.lcd.set_track("File non trovato")
            return
        kind = classify(path)
        eng = self._pick_engine(path)
        if eng is not self.engine:
            self._switch_engine(eng)

        self._current_path = path
        self._ended_handled = False
        self._fallback_tried = False
        self.engine.load(os.path.normpath(path))
        self.playlist.set_current(path)
        name = os.path.basename(path)
        self.lcd.set_track(name)
        self.setWindowTitle(f"{self._base_title} — {name}")
        self.lcd.set_hint(None)
        if kind == "video" and not self.engine.supports_video:
            self.lcd.set_hint("solo audio")

        self._video_forced = None
        self._apply_mode("video" if kind == "video" else "audio")

    def _on_ended(self):
        if self._repeat == "one":
            self.engine.position = 0
            self.engine.play()
            return
        paths = self.playlist.paths()
        if not paths:
            return
        if self._shuffle and len(paths) > 1:
            pool = [p for p in paths if p != self._current_path]
            self.play_path(random.choice(pool))
            return
        i = paths.index(self._current_path) if self._current_path in paths \
            else -1
        nxt = i + 1
        if nxt >= len(paths):
            if self._repeat == "all":
                nxt = 0
            else:
                self.engine.stop()
                return
        self.play_path(paths[nxt])

    def next_track(self):
        paths = self.playlist.paths()
        if not paths:
            return
        if self._shuffle and len(paths) > 1:
            pool = [p for p in paths if p != self._current_path]
            self.play_path(random.choice(pool))
            return
        i = paths.index(self._current_path) if self._current_path in paths \
            else -1
        self.play_path(paths[(i + 1) % len(paths)])

    def prev_track(self):
        if self._current_path and self.engine.position > 3.0:
            self.engine.position = 0
            return
        paths = self.playlist.paths()
        if not paths:
            return
        if self._shuffle and len(paths) > 1:
            pool = [p for p in paths if p != self._current_path]
            self.play_path(random.choice(pool))
            return
        i = paths.index(self._current_path) if self._current_path in paths \
            else 0
        self.play_path(paths[(i - 1) % len(paths)])

    # ------------------------------------------------------------------ seek
    def _seek_preview(self, value):
        dur = self.engine.duration
        if dur > 0:
            self.lcd.set_time(value / 1000.0 * dur, dur)

    def _seek_release(self):
        self._seeking = False
        dur = self.engine.duration
        if dur > 0:
            self.engine.position = self.progress.value() / 1000.0 * dur

    def seek_relative(self, seconds):
        self.engine.position = max(0.0, self.engine.position + seconds)

    # ---------------------------------------------------------------- volume
    def _set_volume(self, v):
        self.engine.volume = v
        if self._muted and v > 0:
            self._muted = False
            self.engine.mute = False
            self.btn_mute.setChecked(False)
            self.btn_mute.set_glyph(SPEAKER)
            self.lcd.set_muted(False)

    def volume_relative(self, delta):
        self.volume.setValue(max(0, min(100, self.volume.value() + delta)))

    def toggle_mute(self):
        self._muted = not self._muted
        self.engine.mute = self._muted
        self.btn_mute.setChecked(self._muted)
        self.btn_mute.set_glyph(SPEAKER_MUTE if self._muted else SPEAKER)
        self.lcd.set_muted(self._muted)

    # ------------------------------------------------------------- velocita'
    def _set_speed(self, idx):
        self._rate_idx = max(0, min(len(RATE_STEPS) - 1, idx))
        r = RATE_STEPS[self._rate_idx]
        self.engine.rate = r
        self.rate_label.setText(f"{r:.2f}×")
        self.lcd.set_rate(r)

    # ----------------------------------------------------- shuffle / repeat
    def toggle_shuffle(self):
        self._shuffle = not self._shuffle
        self.btn_shuffle.setChecked(self._shuffle)
        self.lcd.set_shuffle(self._shuffle)

    def cycle_repeat(self):
        self._repeat = {"off": "all", "all": "one", "one": "off"}[self._repeat]
        self.btn_repeat.setChecked(self._repeat != "off")
        self.btn_repeat.set_glyph(REPEAT_ONE if self._repeat == "one"
                                  else REPEAT)
        self.lcd.set_repeat(self._repeat)

    # ------------------------------------------------------------- finestra
    def toggle_playlist(self):
        if self._fs_active:
            return
        show = not self.playlist.isVisible()
        self.playlist.setVisible(show)
        self.btn_playlist.setChecked(show)
        if not self.isFullScreen():
            delta = min(220, self.playlist.sizeHint().height() or 180)
            self.resize(self.width(), max(self.minimumHeight(),
                                          self.height() + (delta if show
                                                           else -delta)))

    def toggle_video_panel(self):
        self._video_forced = not self.video_panel.isVisible() \
            if self._video_forced is None else not self._video_forced
        if self._video_forced and self._video_widget is None:
            self.lcd.set_hint("niente video")
            self._video_forced = None
            self.btn_monitor.setChecked(False)
            return
        self._apply_mode(self._mode)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self._leave_fullscreen()
        elif self.video_panel.isVisible():
            self._fs_was_max = self.isMaximized()
            self.showFullScreen()
            self._fs_apply(True)

    def _leave_fullscreen(self):
        if self.isFullScreen():
            if self._fs_was_max:
                self.showMaximized()
            else:
                self.showNormal()
        self._fs_apply(False)

    def changeEvent(self, ev):
        # copre anche l'uscita fatta dal sistema (Win+Freccia, Alt+Tab...)
        if ev.type() == QEvent.Type.WindowStateChange:
            self._fs_apply(self.isFullScreen())
        super().changeEvent(ev)

    def _fs_apply(self, on):
        if on == self._fs_active or not hasattr(self, "bar_widget"):
            return
        self._fs_active = on
        lay = self.centralWidget().layout()
        if on:
            self._fs_pl = self.playlist.isVisible()
            self._video_qss = self.video_panel.styleSheet()
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            self.lcd.hide()
            self.util_widget.hide()
            self.playlist.hide()
            self.video_stack.setContentsMargins(0, 0, 0, 0)
            self.video_panel.setStyleSheet(
                "#videoPanel { background-color: #000000; border: none; }")
            self.bar_widget.layout().setContentsMargins(18, 8, 18, 14)
            self.bar_widget.show()
            self._fs_last_pos = QCursor.pos()
            self._fs_idle = time.monotonic()
        else:
            lay.setContentsMargins(10, 10, 10, 10)
            lay.setSpacing(8)
            self.lcd.show()
            self.util_widget.show()
            self.playlist.setVisible(self._fs_pl)
            self.video_stack.setContentsMargins(1, 1, 1, 1)
            self.video_panel.setStyleSheet(self._video_qss)
            self.bar_widget.layout().setContentsMargins(0, 0, 0, 0)
            self.bar_widget.show()
            self.unsetCursor()

    def _fs_show_bar(self, visible):
        if self.bar_widget.isVisible() != visible:
            self.bar_widget.setVisible(visible)
        if visible:
            self.unsetCursor()
        else:
            self.setCursor(Qt.CursorShape.BlankCursor)

    def _fs_tick(self, st):
        if not self._fs_active:
            return
        pos, now = QCursor.pos(), time.monotonic()
        if pos != self._fs_last_pos or st != PS_PLAYING or self._seeking:
            self._fs_last_pos, self._fs_idle = pos, now
            self._fs_show_bar(True)
        elif now - self._fs_idle > 2.5 and not self.bar_widget.underMouse():
            self._fs_show_bar(False)

    def toggle_on_top(self):
        self._on_top = not self._on_top
        fs = self.isFullScreen()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._on_top)
        self.show()
        if fs:   # setWindowFlag ricrea la finestra e fa perdere il fullscreen
            self.showFullScreen()

    def _escape(self):
        if self.isFullScreen():
            self.showNormal()

    # ----------------------------------------------------------------- file
    def open_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Apri file multimediali",
                                                "", MEDIA_FILTER_ALL)
        if not paths:
            return
        for p in paths:
            self.playlist.add_path(p)
        self.play_path(paths[0])

    def open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Apri cartella")
        if not d:
            return
        files = _media_files(d)
        if not files:
            self.lcd.set_hint("cartella vuota")
            return
        for p in files:
            self.playlist.add_path(p)
        self.play_path(files[0])

    def _on_paths_added(self, added):
        if added and self._current_path is None:
            self.play_path(added[0])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        added = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                p = url.toLocalFile()
                self.playlist.add_path(p)
                added.append(p)
        if added:
            self._on_paths_added(added)

    # ------------------------------------------------------------------ tick
    def _update(self):
        st = self.engine.play_state
        self.btn_play.set_glyph(PAUSE if st == PS_PLAYING else PLAY)

        dur = self.engine.duration
        pos = self.engine.position
        if dur > 0 and not self._seeking:
            self.progress.blockSignals(True)
            self.progress.setValue(int(pos / dur * 1000))
            self.progress.blockSignals(False)
        self.lcd.set_time(pos, dur)
        self.lcd.set_state(STATE_TEXT.get(st, "Pronto"),
                           STATE_KIND.get(st, "stop"))

        # VU decorativi (il WMP COM non espone i livelli audio reali)
        if st == PS_PLAYING:
            self._vu_l += (random.uniform(0.3, 0.95) - self._vu_l) * 0.45
            self._vu_r += (random.uniform(0.25, 0.9) - self._vu_r) * 0.45
        else:
            self._vu_l *= 0.7
            self._vu_r *= 0.7
        self.lcd.set_vu(self._vu_l, self._vu_r)

        if st == PS_PLAYING:
            self._ended_handled = False
        elif st == PS_MEDIAENDED and not self._ended_handled:
            self._ended_handled = True
            self._on_ended()

        if getattr(self.engine, "error", False):
            self._retry_with_qt()
        self._fs_tick(st)

    # ------------------------------------------------------------ persistenza
    def _restore_settings(self):
        self.volume.setValue(int(self.store.value("volume", 100)))
        self._muted = self.store.value("mute", False, type=bool)
        self._shuffle = self.store.value("shuffle", False, type=bool)
        self._repeat = str(self.store.value("repeat", "off"))
        self._rate_idx = int(self.store.value("rate_idx", 2))
        self._on_top = self.store.value("on_top", False, type=bool)

        self.btn_mute.setChecked(self._muted)
        self.btn_mute.set_glyph(SPEAKER_MUTE if self._muted else SPEAKER)
        self.lcd.set_muted(self._muted)
        self.lcd.set_shuffle(self._shuffle)
        self.lcd.set_repeat(self._repeat)
        self.btn_shuffle.setChecked(self._shuffle)
        self.btn_repeat.setChecked(self._repeat != "off")
        self.btn_repeat.set_glyph(REPEAT_ONE if self._repeat == "one"
                                  else REPEAT)
        self.btn_pin.setChecked(self._on_top)
        if self._on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._set_speed(self._rate_idx)

    def _save_settings(self):
        self.store.setValue("volume", self.volume.value())
        self.store.setValue("mute", self._muted)
        self.store.setValue("shuffle", self._shuffle)
        self.store.setValue("repeat", self._repeat)
        self.store.setValue("rate_idx", self._rate_idx)
        self.store.setValue("on_top", self._on_top)

    def closeEvent(self, ev):
        self._save_settings()
        self._timer.stop()
        try:
            self.engine.stop()
        except Exception:
            pass
        if self._eng_video is not None and self._eng_video is not self.engine:
            try:
                self._eng_video.stop()
            except Exception:
                pass
        if hasattr(self._eng_video, "shutdown"):
            try:
                self._eng_video.shutdown()
            except Exception:
                pass
        if hasattr(self._eng_audio, "close"):
            try:
                self._eng_audio.close()
            except Exception:
                pass
        super().closeEvent(ev)
