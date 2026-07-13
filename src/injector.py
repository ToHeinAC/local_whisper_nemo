"""Type transcribed text into whatever field currently has focus.

Uses the Windows SendInput API with Unicode key events. This sends real
keystrokes (landing at the active cursor in Word, browsers, ...) and handles
Unicode incl. German umlauts (äöüß). We deliberately do NOT use
``keyboard.write`` here: with a global hook active it duplicates characters.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# Virtual-key codes for the special keys spoken commands can trigger.
_VK = {"enter": 0x0D, "tab": 0x09}

ULONG_PTR = ctypes.c_size_t  # pointer-sized, matches Win32 ULONG_PTR


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MOUSEINPUT(ctypes.Structure):
    # Included only so the INPUT union has its true (largest) size, making
    # sizeof(_INPUT) match what SendInput's cbSize check expects.
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT)]

    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


_user32 = ctypes.windll.user32
_user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
_user32.SendInput.restype = wintypes.UINT


def _key_event(scan: int, key_up: bool) -> _INPUT:
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0)
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp.ki = _KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
    return inp


def _vk_event(vk: int, key_up: bool) -> _INPUT:
    flags = KEYEVENTF_KEYUP if key_up else 0
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp.ki = _KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
    return inp


class TextInjector:
    def __init__(self, type_delay: float = 0.0) -> None:
        self._type_delay = type_delay

    def _send_char(self, ch: str) -> None:
        events = (_INPUT * 2)(_key_event(ord(ch), False), _key_event(ord(ch), True))
        sent = _user32.SendInput(2, events, ctypes.sizeof(_INPUT))
        if sent != 2:
            raise ctypes.WinError(ctypes.get_last_error())

    def press(self, key: str) -> None:
        """Press and release a special key (`"enter"` or `"tab"`)."""
        vk = _VK[key]
        events = (_INPUT * 2)(_vk_event(vk, False), _vk_event(vk, True))
        sent = _user32.SendInput(2, events, ctypes.sizeof(_INPUT))
        if sent != 2:
            raise ctypes.WinError(ctypes.get_last_error())

    def inject(self, text: str) -> None:
        """Type `text` at the current cursor position."""
        if not text:
            return
        for ch in text:
            self._send_char(ch)
            if self._type_delay:
                time.sleep(self._type_delay)
