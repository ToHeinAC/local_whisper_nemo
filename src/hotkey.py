"""Global push-to-talk listener.

Platform backends, selected at import:

- Windows: `hotkey_keyboard` — the `keyboard` library's global hooks.
- macOS: `hotkey_darwin` — a pynput `Listener` tracking held keys.

Both expose `PushToTalk(combo, start_cb, stop_cb)`: `start_cb` fires when the
combo goes down, `stop_cb` when the trigger key (the last key of the combo) is
released. `start()` registers the hooks without blocking and raises `ValueError`
if the combo names a key the backend does not know.
"""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .hotkey_keyboard import PushToTalk
elif sys.platform == "darwin":
    from .hotkey_darwin import PushToTalk
else:
    raise ImportError(f"No global hotkey backend for platform {sys.platform!r}")

__all__ = ["PushToTalk"]
