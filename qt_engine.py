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

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QMediaMetaData
from PySide6.QtMultimediaWidgets import QVideoWidget

# Unifica gli stati con engine.py
PS_STOPPED, PS_PAUSED, PS_PLAYING, PS_MEDIAENDED = 1, 2, 3, 8

_STATE_MAP = {
    QMediaPlayer.PlaybackState.StoppedState: PS_STOPPED,
    QMediaPlayer.PlaybackState.PausedState: PS_PAUSED,
    QMediaPlayer.PlaybackState.PlayingState: PS_PLAYING,
}


class QtMediaEngine:
    engine_name = "QT « "
    supports_video = True

    def __init__(self):
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._audio.setVolume(1.0)
        self._player.setAudioOutput(self._audio)
        self._video = QVideoWidget()
        self._video.setStyleSheet("background-color:#000000;")
        self._player.setVideoOutput(self._video)
        # QMediaPlayer non ha uno stato "fine brano": lo si ricava dal segnale
        # e lo si espone come PS_MEDIAENDED (senza, scaletta/ripeti non
        # avanzavano a fine video).
        self._ended = False
        self._error = False
        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.errorOccurred.connect(self._on_error)

    def _on_status(self, st):
        if st == QMediaPlayer.MediaStatus.EndOfMedia:
            self._ended = True

    def _on_error(self, *args):
        self._error = True

    @property
    def error(self):
        return self._error

    @property
    def version(self):
        from PySide6.QtCore import QT_VERSION_STR
        return QT_VERSION_STR

    @property
    def widget(self):
        """Il QVideoWidget da innestare nel pannello video del player."""
        return self._video

    def load(self, path):
        self._ended = False
        self._error = False
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()  # autoStart, come il motore WMP

    def play(self):
        self._ended = False
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._ended = False
        self._player.stop()

    @property
    def play_state(self):
        st = _STATE_MAP.get(self._player.playbackState(), PS_STOPPED)
        if self._ended and st == PS_STOPPED:
            return PS_MEDIAENDED
        return st

    @property
    def duration(self):
        try:
            return self._player.duration() / 1000.0
        except (TypeError, ValueError):
            return 0.0

    @property
    def position(self):
        try:
            return self._player.position() / 1000.0
        except (TypeError, ValueError):
            return 0.0

    @position.setter
    def position(self, seconds):
        self._ended = False
        self._player.setPosition(int(seconds * 1000))

    @property
    def volume(self):
        return int(round(self._audio.volume() * 100))

    @volume.setter
    def volume(self, v):
        self._audio.setVolume(max(0, min(100, int(v))) / 100.0)

    @property
    def mute(self):
        return self._audio.isMuted()

    @mute.setter
    def mute(self, v):
        self._audio.setMuted(bool(v))

    @property
    def rate(self):
        return float(self._player.playbackRate())

    @rate.setter
    def rate(self, v):
        self._player.setPlaybackRate(float(v))

    def shutdown(self):
        self._player.stop()
        self._player.setSource(QUrl())
