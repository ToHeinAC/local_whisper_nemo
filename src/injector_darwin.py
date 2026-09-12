"""Type transcribed text at the cursor on macOS.

Uses pynput, which posts Quartz `CGEvent`s carrying a Unicode payload rather
than a key code, so umlauts (äöüß) arrive intact whatever keyboard layout is
active — the macOS counterpart of the Win32 `KEYEVENTF_UNICODE` path.

The posting process needs the **Accessibility** permission (System Settings →
Privacy & Security → Accessibility); without it macOS silently drops the events
and nothing is typed.
"""

from __future__ import annotations

import time

from pynput.keyboard import Controller, Key

# Keys the spoken commands can trigger (mirrors injector_win32._VK).
_KEYS = {"enter": Key.enter, "tab": Key.tab}


class TextInjector:
    def __init__(self, type_delay: float = 0.0) -> None:
        self._type_delay = type_delay
        self._keyboard = Controller()

    def _send_char(self, ch: str) -> None:
        self._keyboard.type(ch)

    def press(self, key: str) -> None:
        """Press and release a special key (`"enter"` or `"tab"`)."""
        self._keyboard.tap(_KEYS[key])

    def inject(self, text: str) -> None:
        """Type `text` at the current cursor position."""
        if not text:
            return
        for ch in text:
            self._send_char(ch)
            if self._type_delay:
                time.sleep(self._type_delay)
