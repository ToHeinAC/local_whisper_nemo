"""Overlay level-scaling logic (no Tk window created)."""

import sys
from unittest.mock import MagicMock

import pytest

from src.overlay import Overlay, scale_level


def test_scale_level_clamps_to_unit_range():
    assert scale_level(0.0) == 0.0
    assert scale_level(1.0) == 1.0  # already loud -> clamped
    assert scale_level(-0.5) == 0.0


def test_scale_level_applies_gain():
    assert scale_level(0.05, gain=8.0) == 0.4


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS window handling")
def test_macos_show_and_hide_never_reorder_the_window():
    """Re-ordering drops the focused app's key status and nothing then holds
    keyboard focus, so the injected transcript goes nowhere."""
    ov = Overlay.__new__(Overlay)  # no Tk: only the show/hide policy is under test
    ov.root = MagicMock()

    ov._show_window()
    ov._hide_window()

    ov.root.deiconify.assert_not_called()
    ov.root.withdraw.assert_not_called()
    assert [c.args for c in ov.root.attributes.call_args_list] == [
        ("-alpha", 1.0),
        ("-alpha", 0.0),
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows window handling")
def test_windows_show_and_hide_use_deiconify_and_withdraw():
    ov = Overlay.__new__(Overlay)
    ov.root = MagicMock()

    ov.root.state.return_value = "withdrawn"
    ov._show_window()
    ov.root.deiconify.assert_called_once()

    ov.root.state.return_value = "normal"
    ov._hide_window()
    ov.root.withdraw.assert_called_once()
