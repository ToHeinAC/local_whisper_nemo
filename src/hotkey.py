"""Global push-to-talk listener.

`start_cb` fires when the combo is pressed; `stop_cb` fires when the trigger key
(the last key of the combo, e.g. `shift` in `ctrl+shift`) is released. An
active flag prevents duplicate start/stop while the combo is held.

Pure-modifier combos like `ctrl+shift` work: the `keyboard` library treats
modifiers as ordinary keys, so `shift` is a valid trigger key.
"""

from __future__ import annotations

from typing import Callable

import keyboard


class PushToTalk:
    def __init__(
        self,
        combo: str,
        start_cb: Callable[[], None],
        stop_cb: Callable[[], None],
    ) -> None:
        self._combo = combo
        self._trigger_key = combo.split("+")[-1].strip()
        self._start_cb = start_cb
        self._stop_cb = stop_cb
        self._active = False

    def _on_combo(self) -> None:
        if not self._active:
            self._active = True
            self._start_cb()

    def _on_release(self, _event) -> None:  # noqa: ANN001
        if self._active:
            self._active = False
            self._stop_cb()

    def start(self) -> None:
        """Register global hooks (non-blocking)."""
        keyboard.add_hotkey(self._combo, self._on_combo, trigger_on_release=False)
        keyboard.on_release_key(self._trigger_key, self._on_release)
