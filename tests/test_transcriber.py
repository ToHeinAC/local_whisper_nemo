"""Transcriber tests.

The empty-input path is fast and device-free. The real-model path is marked
`slow` because it downloads and runs the actual Nemotron model.
"""

import numpy as np
import pytest

from src.config import load_settings
from src.transcriber import Transcriber


def test_empty_audio_returns_empty_without_loading_model():
    # Build a Transcriber without invoking __init__ to avoid loading a model.
    t = Transcriber.__new__(Transcriber)
    assert t.transcribe(np.zeros(0, dtype=np.float32)) == ""


@pytest.mark.slow
def test_real_model_returns_string_on_silence():
    settings = load_settings()
    transcriber = Transcriber(settings)
    # One second of silence -> a string (possibly empty), never an error.
    audio = np.zeros(settings.sample_rate, dtype=np.float32)
    assert isinstance(transcriber.transcribe(audio), str)
