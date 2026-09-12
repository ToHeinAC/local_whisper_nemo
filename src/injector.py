"""Type transcribed text into whatever field currently has focus.

Platform backends, selected at import:

- Windows: `injector_win32` — Win32 `SendInput` with Unicode key events.
- macOS: `injector_darwin` — pynput/Quartz `CGEvent`s.

Both expose `TextInjector` with `inject(text)` and `press(key)`.
"""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from .injector_win32 import TextInjector
elif sys.platform == "darwin":
    from .injector_darwin import TextInjector
else:
    raise ImportError(f"No text injection backend for platform {sys.platform!r}")

__all__ = ["TextInjector"]
