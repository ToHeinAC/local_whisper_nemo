"""Recorder buffer logic — no real audio device required."""

import numpy as np
import pytest

from src.recorder import AudioRecorder


def test_empty_recording_returns_empty_float32():
    rec = AudioRecorder(sample_rate=16000)
    out = rec.stop()
    assert out.dtype == np.float32
    assert out.size == 0


def test_callback_chunks_are_concatenated_as_mono():
    rec = AudioRecorder(sample_rate=16000)
    rec._chunks = []
    frame_a = np.array([[0.1], [0.2]], dtype=np.float32)
    frame_b = np.array([[0.3]], dtype=np.float32)

    rec._callback(frame_a, len(frame_a), None, None)
    rec._callback(frame_b, len(frame_b), None, None)
    out = rec.stop()

    assert out.dtype == np.float32
    np.testing.assert_allclose(out, [0.1, 0.2, 0.3])


def test_level_tracks_peak_of_latest_chunk():
    rec = AudioRecorder(sample_rate=16000)
    rec._chunks = []
    rec._callback(np.array([[0.1], [-0.4]], dtype=np.float32), 2, None, None)
    assert rec.level() == pytest.approx(0.4)
    # stop() resets the level for the meter
    rec.stop()
    assert rec.level() == 0.0
