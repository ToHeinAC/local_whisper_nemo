"""macOS hotkey backend: combo parsing and the hold/release state machine."""

import sys
from types import SimpleNamespace

import pytest

if sys.platform != "darwin":
    pytest.skip("macOS hotkey backend", allow_module_level=True)

from pynput.keyboard import Key, KeyCode  # noqa: E402

from src.hotkey_darwin import PushToTalk, _name, _parse_combo  # noqa: E402


def test_combo_splits_into_canonical_names():
    assert _parse_combo("ctrl+shift") == ["ctrl", "shift"]
    assert _parse_combo("ctrl+alt+space") == ["ctrl", "alt", "space"]


def test_macos_aliases_and_case_are_accepted():
    assert _parse_combo("Command+Option+D") == ["cmd", "alt", "d"]


def test_unknown_key_name_raises_value_error():
    with pytest.raises(ValueError, match="nope"):
        _parse_combo("ctrl+nope")


def test_left_right_modifier_variants_collapse():
    assert _name(Key.ctrl_r) == "ctrl"
    assert _name(Key.shift_l) == "shift"
    assert _name(Key.cmd_r) == "cmd"
    assert _name(Key.space) == "space"
    assert _name(KeyCode.from_char("A")) == "a"
    assert _name(KeyCode(vk=1, char=None)) is None


def _armed(combo="ctrl+shift"):
    """A PushToTalk wired up as `start()` leaves it, minus the real listener."""
    events = []
    ptt = PushToTalk(
        combo, lambda: events.append("start"), lambda: events.append("stop")
    )
    ptt._keys = _parse_combo(combo)
    ptt._listener = SimpleNamespace(canonical=lambda key: key)
    return ptt, events


def test_start_fires_only_once_the_combo_is_complete():
    ptt, events = _armed()
    ptt._on_press(Key.ctrl_l)
    assert events == []
    ptt._on_press(Key.shift_r)
    assert events == ["start"]
    ptt._on_press(Key.ctrl_l)  # auto-repeat must not re-fire
    assert events == ["start"]


def test_stop_fires_when_the_trigger_key_is_released():
    ptt, events = _armed()
    ptt._on_press(Key.ctrl_l)
    ptt._on_press(Key.shift_l)
    ptt._on_release(Key.ctrl_l)  # not the trigger key
    assert events == ["start"]
    ptt._on_release(Key.shift_l)
    assert events == ["start", "stop"]


def test_release_without_an_active_combo_is_ignored():
    ptt, events = _armed()
    ptt._on_press(Key.shift_l)
    ptt._on_release(Key.shift_l)
    assert events == []
