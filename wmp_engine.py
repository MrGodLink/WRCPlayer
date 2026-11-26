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

try:
    import win32com.client
    from pywintypes import com_error
    _COM_OK = True
except ImportError:
    _COM_OK = False

    class com_error(Exception):
        """Segnaposto per i sistemi senza pywin32."""

WMP_PROGID = "WMPlayer.OCX.7"

# playState (Microsoft): 1 Stopped, 2 Paused, 3 Playing, 8 MediaEnded,
# 9 Transitioning, 10 Ready. Non affidarsi all'ordine degli stati.
PS_STOPPED, PS_PAUSED, PS_PLAYING, PS_MEDIAENDED = 1, 2, 3, 8

_MISSING_MSG = ("Windows Media Player Legacy non installato: Impostazioni > "
                "Sistema > Funzionalita' facoltative (edizioni N: Media "
                "Feature Pack)")


def _make_events(eng):
    """Gestore eventi COM. Qui NON si chiamano metodi COM (rientranza):
    si memorizza solo lo stato, che il player legge al tick successivo."""
    class _Events:
        def OnPlayStateChange(self, new_state):
            eng._on_state(int(new_state))

        def OnMediaError(self, item):
            eng._error = True
    return _Events


class WmpEngine:
    engine_name = "WPM « "
    supports_video = False

    def __init__(self):
        if not _COM_OK:
            raise RuntimeError("pywin32 non disponibile su questo sistema")
        self._state = 0
        self._ended = False
        self._error = False
        self._dur = 0.0
        self._last_pos = 0.0
        self._events = False
        try:
            self._w = win32com.client.DispatchWithEvents(
                WMP_PROGID, _make_events(self))
            self._events = True
        except Exception:
            try:
                self._w = win32com.client.Dispatch(WMP_PROGID)
            except com_error as e:
                raise RuntimeError(_MISSING_MSG) from e
        for name, val in (("autoStart", True), ("volume", 100),
                          ("enableErrorDialogs", False),
                          ("invokeURLs", False)):
            try:
                setattr(self._w.settings, name, val)
            except com_error:
                pass

    # --- eventi / stato ------------------------------------------------------
    def _on_state(self, s):
        self._state = s
        if s == PS_MEDIAENDED:
            self._ended = True
        elif s == PS_PLAYING:
            self._ended = False

    @property
    def error(self):
        return self._error

    @property
    def version(self):
        try:
            return self._w.versionInfo
        except com_error:
            return None

    def load(self, path):
        self._ended = False
        self._error = False
        self._dur = 0.0
        self._last_pos = 0.0
        # Assegna URL; con autoStart=True avvia la riproduzione (asincrona).
        self._w.URL = path

    def play(self):
        self._ended = False
        try:
            self._w.controls.play()
        except com_error:
            pass

    def pause(self):
        try:
            self._w.controls.pause()
        except com_error:
            pass

    def stop(self):
        self._ended = False
        try:
            self._w.controls.stop()
        except com_error:
            pass

    @property
    def play_state(self):
        if self._events:
            if self._ended and self._state != PS_PLAYING:
                return PS_MEDIAENDED
            return self._state
        return self._poll_state()

    def _poll_state(self):
        """Fallback senza eventi: polling + fine brano dedotta."""
        try:
            st = int(self._w.playState)
        except (com_error, TypeError, ValueError):
            return 0
        if st == PS_MEDIAENDED:
            self._ended = True
        elif st == PS_PLAYING:
            self._ended = False
        elif (self._state == PS_PLAYING and st != PS_PAUSED
              and self._dur > 0 and self._last_pos >= self._dur - 1.0):
            self._ended = True      # MediaEnded perso tra due tick
        self._state = st
        return PS_MEDIAENDED if (self._ended and st != PS_PLAYING) else st

    @property
    def duration(self):
        if self._dur > 0:
            return self._dur
        try:
            m = self._w.currentMedia
            self._dur = float(m.duration) if m is not None else 0.0
        except (com_error, TypeError, ValueError):
            self._dur = 0.0
        return self._dur

    @property
    def position(self):
        if self._state == PS_STOPPED:
            return 0.0
        try:
            self._last_pos = float(self._w.controls.currentPosition)
        except (com_error, TypeError, ValueError):
            pass
        return self._last_pos

    @position.setter
    def position(self, seconds):
        try:
            self._w.controls.currentPosition = float(seconds)
            self._last_pos = float(seconds)
        except com_error:
            pass

    @property
    def volume(self):
        try:
            return int(self._w.settings.volume)
        except (com_error, TypeError, ValueError):
            return 0

    @volume.setter
    def volume(self, v):
        try:
            self._w.settings.volume = int(max(0, min(100, v)))
            if v > 0:
                self._w.settings.mute = False
        except com_error:
            pass

    @property
    def mute(self):
        try:
            return bool(self._w.settings.mute)
        except com_error:
            return False

    @mute.setter
    def mute(self, v):
        try:
            self._w.settings.mute = bool(v)
        except com_error:
            pass

    @property
    def rate(self):
        try:
            return float(self._w.settings.rate)
        except (com_error, TypeError, ValueError):
            return 1.0

    @rate.setter
    def rate(self, v):
        try:
            self._w.settings.rate = float(max(0.25, min(2.0, v)))
        except com_error:
            pass

    def close(self):
        """Rilascia l'OCX (chiamare alla chiusura, dopo aver fermato i timer)."""
        w, self._w = self._w, None
        if w is None:
            return
        try:
            w.controls.stop()
            w.close()
        except Exception:
            pass
