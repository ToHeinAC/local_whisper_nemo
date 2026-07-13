"""System-tray icon with a Quit action.

pystray's `run()` blocks, so the icon runs on its own thread (`run_detached`).
"""

from __future__ import annotations

from typing import Callable

import pystray
from PIL import Image, ImageDraw


def _make_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), "#202020")
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill="#e53935")  # red mic dot
    return img


def create_tray(on_quit: Callable[[], None]) -> pystray.Icon:
    """Build (but do not start) the tray icon."""
    def _quit(icon: pystray.Icon, _item) -> None:  # noqa: ANN001
        icon.stop()
        on_quit()

    menu = pystray.Menu(pystray.MenuItem("Quit", _quit))
    return pystray.Icon("local_whisper", _make_icon_image(), "local_whisper", menu)
