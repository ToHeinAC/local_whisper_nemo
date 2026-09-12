"""Global push-to-talk listener for macOS (pynput).

pynput has no press-and-hold hotkey primitive, so we watch raw key events and
track which of the combo's keys are currently held: the combo going complete
fires `start_cb`, releasing the trigger key fires `stop_cb`. Key names are the
same ones the Windows backend accepts (`ctrl+shift`, `ctrl+alt+space`), with
`cmd` — and the usual macOS aliases — recognised on top.

The listening process needs the **Input Monitoring** permission (System
Settings → Privacy & Security → Input Monitoring); without it the listener
starts but never sees a key.
"""

from __future__ import annotations

from typing import Callable

from pynput.keyboard import Key, KeyCode, Listener

# Left/right variants collapse onto these, so `ctrl` matches either Ctrl key.
_MODIFIERS = ("ctrl", "shift", "alt", "cmd")

# Spellings accepted in HOTKEY on top of pynput's own `Key` names.
_ALIASES = {
    "control": "ctrl",
    "option": "alt",
    "opt": "alt",
    "command": "cmd",
    "super": "cmd",
    "win": "cmd",
    "windows": "cmd",
    "return": "enter",
}


def _name(key: Key | KeyCode | None) -> str | None:
    """Canonical name of a pressed key, or None if it has no printable form."""
    if isinstance(key, KeyCode):
        return key.char.lower() if key.char else None
    if key is None:
        return None
    for base in _MODIFIERS:
        if key.name.startswith(base):  # ctrl_l, shift_r, alt_gr, cmd_r, ...
            return base
    return key.name


def _parse_combo(combo: str) -> list[str]:
    """Split `"ctrl+alt+space"` into canonical key names, validating each."""
    names = []
    for part in combo.split("+"):
        name = part.strip().lower()
        name = _ALIASES.get(name, name)
        if name not in _MODIFIERS and not hasattr(Key, name) and len(name) != 1:
            raise ValueError(f"unknown key name {part.strip()!r}")
        names.append(name)
    return names


class PushToTalk:
    def __init__(
        self,
        combo: str,
        start_cb: Callable[[], None],
        stop_cb: Callable[[], None],
    ) -> None:
        self._combo = combo
        self._start_cb = start_cb
        self._stop_cb = stop_cb
        self._active = False
        self._keys: list[str] = []
        self._held: set[str] = set()
        self._listener: Listener | None = None

    def _canonical_name(self, key: Key | KeyCode | None) -> str | None:
        # Listener.canonical strips the modifiers macOS folds into a KeyCode,
        # so `a` stays `a` while ctrl is down instead of arriving as "\x01".
        return _name(self._listener.canonical(key))

    def _on_press(self, key: Key | KeyCode | None) -> None:
        name = self._canonical_name(key)
        if name is None:
            return
        self._held.add(name)
        if not self._active and self._held.issuperset(self._keys):
            self._active = True
            self._start_cb()

    def _on_release(self, key: Key | KeyCode | None) -> None:
        name = self._canonical_name(key)
        if name is None:
            return
        self._held.discard(name)
        if self._active and name == self._keys[-1]:
            self._active = False
            self._stop_cb()

    def start(self) -> None:
        """Register global hooks (non-blocking)."""
        self._keys = _parse_combo(self._combo)
        self._listener = Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
