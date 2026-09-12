"""Injector tests — the low-level send is mocked (no real keystrokes sent)."""

import sys
from unittest.mock import patch

import pytest

from src.injector import TextInjector


def test_empty_text_sends_nothing():
    with patch.object(TextInjector, "_send_char") as send:
        TextInjector().inject("")
        send.assert_not_called()


def test_each_character_is_sent_once():
    text = "Grüße"
    with patch.object(TextInjector, "_send_char") as send:
        TextInjector().inject(text)
        assert [c.args[0] for c in send.call_args_list] == list(text)


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 backend")
def test_press_maps_known_keys_to_virtual_key_codes():
    from src.injector_win32 import _VK

    assert _VK == {"enter": 0x0D, "tab": 0x09}


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS backend")
def test_press_maps_known_keys_to_pynput_keys():
    from pynput.keyboard import Key

    from src.injector_darwin import _KEYS

    assert _KEYS == {"enter": Key.enter, "tab": Key.tab}
