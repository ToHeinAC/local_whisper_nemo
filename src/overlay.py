"""Small always-on-top status indicator.

While recording it shows a scrolling waveform of vertical bars that oscillate
with the live microphone level; while transcribing it shows a text label.

Tkinter is not thread-safe, so widgets are only touched on the main thread:
other threads switch the mode via `show_meter()` / `show_text()` / `hide()` and a
periodic poll on the main thread applies it and animates the bars. Run
`mainloop()` on the main thread.
"""

from __future__ import annotations

import os
import sys
from collections import deque
from pathlib import Path
from typing import Callable

if sys.platform == "darwin" and "TCL_LIBRARY" not in os.environ:
    # uv's managed CPython keeps its Tcl under the interpreter's own prefix, but
    # inside a .venv `sys.prefix` points at the venv instead, so Tk() dies with
    # "can't find a usable init.tcl". Point it at the real library before
    # tkinter is imported (the constant is read at import time).
    _tcl = Path(sys.base_prefix) / "lib" / "tcl8.6"
    if _tcl.is_dir():
        os.environ["TCL_LIBRARY"] = str(_tcl)

import tkinter as tk  # noqa: E402

_MACOS = sys.platform == "darwin"
# Where the macOS window sits while "hidden" — far off any screen (see _map_parked).
PARKED = "+-4000+-4000"

BARS = 40
CANVAS_W = 260
CANVAS_H = 70
POLL_MS = 40  # ~25 fps
METER_GAIN = 8.0  # scales raw peak amplitude to bar height
BG = "#202020"


def scale_level(raw: float, gain: float = METER_GAIN) -> float:
    """Map a raw peak amplitude to a clamped 0..1 bar height."""
    return max(0.0, min(1.0, raw * gain))


def _bar_color(level: float) -> str:
    if level > 0.8:
        return "#e53935"  # red
    if level > 0.5:
        return "#fbc02d"  # amber
    return "#43a047"  # green


def _keep_app_unactivatable() -> None:
    """Stop the overlay from stealing keyboard focus (macOS only).

    Showing a Tk window activates the process, moving the frontmost app away
    from the one being dictated into, and the injected keystrokes never reach
    the user's document. Asking for the accessory policy — the role menu-bar
    and background apps use — takes the process out of the activation order and
    drops its Dock icon, which suits a push-to-talk tool.

    For a non-bundled process macOS may settle on `Prohibited` rather than the
    `Accessory` asked for here; both are non-activatable, which is the property
    that matters.

    Must run *after* tkinter is initialised: touching `NSApplication` first
    stops Tk installing its own `TKApplication` subclass, and the first window
    then dies on an unrecognised selector.
    """
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )


class Overlay:
    def __init__(self, level_source: Callable[[], float] | None = None) -> None:
        self._level_source = level_source or (lambda: 0.0)
        self._mode = "hidden"  # hidden | meter | text
        self._applied_mode: str | None = None
        self._text = ""
        self._levels: deque[float] = deque([0.0] * BARS, maxlen=BARS)

        self.root = tk.Tk()
        if _MACOS:
            _keep_app_unactivatable()
        self.root.withdraw()
        self.root.overrideredirect(True)  # borderless
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)

        self._canvas = tk.Canvas(
            self.root, width=CANVAS_W, height=CANVAS_H, bg=BG, highlightthickness=0
        )
        self._label = tk.Label(
            self.root, text="", fg="#ffffff", bg=BG, font=("Segoe UI", 12),
            padx=16, pady=8,
        )

        if _MACOS:
            self._map_parked()

    def _map_parked(self) -> None:
        """Put the window on screen once, transparent and parked (macOS only).

        `deiconify()` runs `makeKeyAndOrderFront:`, which makes the *focused*
        app's window resign key. This window is borderless, so it cannot become
        key itself — leaving nothing holding keyboard focus, and the injected
        transcript goes nowhere. Mapping once at startup keeps that out of the
        dictation path: every later show/hide is an alpha change, which does not
        re-order windows and so never disturbs focus.
        """
        self.root.attributes("-alpha", 0.0)
        self.root.geometry(PARKED)
        self.root.deiconify()

    def _show_window(self) -> None:
        if _MACOS:
            self.root.attributes("-alpha", 1.0)
        elif self.root.state() == "withdrawn":
            self.root.deiconify()

    def _hide_window(self) -> None:
        if _MACOS:
            self.root.attributes("-alpha", 0.0)
            self.root.geometry(PARKED)
        elif self.root.state() != "withdrawn":
            self.root.withdraw()

    def show_meter(self) -> None:
        self._levels = deque([0.0] * BARS, maxlen=BARS)
        self._mode = "meter"

    def show_text(self, text: str) -> None:
        self._text = text
        self._mode = "text"

    def hide(self) -> None:
        self._mode = "hidden"

    def _position_bottom_center(self) -> None:
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{sh - h - 80}")

    def _apply_mode(self) -> None:
        """Swap visible widgets only when the mode changes."""
        if self._mode == "meter":
            self._label.pack_forget()
            self._canvas.pack()
        elif self._mode == "text":
            self._canvas.pack_forget()
            self._label.pack()
        self._applied_mode = self._mode

    def _draw_meter(self) -> None:
        self._levels.append(scale_level(self._level_source()))
        self._canvas.delete("all")
        bw = CANVAS_W / BARS
        cy = CANVAS_H / 2
        max_half = CANVAS_H / 2 - 2
        for i, level in enumerate(self._levels):
            half = max(1.0, level * max_half)
            x0 = i * bw
            self._canvas.create_rectangle(
                x0 + 1, cy - half, x0 + bw - 1, cy + half,
                fill=_bar_color(level), outline="",
            )

    def _poll(self) -> None:
        if self._mode == "hidden":
            self._hide_window()
        else:
            if self._mode != self._applied_mode:
                self._apply_mode()
            if self._mode == "meter":
                self._draw_meter()
            elif self._label.cget("text") != self._text:
                self._label.config(text=self._text)
            self._show_window()
            self._position_bottom_center()
        self.root.after(POLL_MS, self._poll)

    def mainloop(self) -> None:
        self.root.after(POLL_MS, self._poll)
        self.root.mainloop()

    def stop(self) -> None:
        self.root.after(0, self.root.destroy)
