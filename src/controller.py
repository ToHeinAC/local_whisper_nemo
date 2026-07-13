"""Dictation state machine: record -> transcribe -> inject -> log.

Kept free of threading and global hooks so it can be unit-tested with mocks.
`main.py` drives it from the hotkey listener.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .commands import parse
from .injector import TextInjector
from .overlay import Overlay
from .recorder import AudioRecorder
from .session_log import SessionLogger
from .transcriber import Transcriber

log = logging.getLogger(__name__)


class Controller:
    def __init__(
        self,
        recorder: AudioRecorder,
        transcriber: Transcriber,
        injector: TextInjector,
        logger: SessionLogger,
        overlay: Overlay,
    ) -> None:
        self._recorder = recorder
        self._transcriber = transcriber
        self._injector = injector
        self._logger = logger
        self._overlay = overlay
        self._busy = False
        self._start: datetime | None = None

    def on_press(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._start = datetime.now()
        log.info("hotkey down -> recording started")
        self._overlay.show_meter()
        self._recorder.start()

    def on_release(self) -> None:
        if not self._busy:
            return
        try:
            audio = self._recorder.stop()
            log.info("hotkey up -> captured %d samples, transcribing", audio.size)
            self._overlay.show_text("… Transcribing")
            text = self._transcriber.transcribe(audio)
            log.info("transcript: %r", text)
            if text:
                for kind, value in parse(text):
                    if kind == "text":
                        self._injector.inject(value)
                    else:
                        self._injector.press(value)
                log.info("typed %d chars", len(text))
            self._logger.record(self._start, datetime.now(), len(text))
        except Exception:  # noqa: BLE001
            log.exception("dictation cycle failed")
        finally:
            self._overlay.hide()
            self._busy = False
