"""Overlay level-scaling logic (no Tk window created)."""

from src.overlay import scale_level


def test_scale_level_clamps_to_unit_range():
    assert scale_level(0.0) == 0.0
    assert scale_level(1.0) == 1.0  # already loud -> clamped
    assert scale_level(-0.5) == 0.0


def test_scale_level_applies_gain():
    assert scale_level(0.05, gain=8.0) == 0.4
