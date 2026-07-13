"""Transcriber tests.

The empty-input path is fast and device-free. The real-model paths are marked
`slow` because they load the actual Nemotron model (from the local cache).
"""

import logging

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


@pytest.mark.slow
def test_model_loads_without_touching_the_network(caplog):
    """The app must run fully offline: loading may only read the local cache.

    Without local_files_only, from_pretrained revalidates every config file
    against the HF Hub on each start. The HTTP client logs one record per
    request, so an empty log proves nothing was fetched.
    """
    with caplog.at_level(logging.INFO):
        Transcriber(load_settings())

    http_records = [
        r.getMessage() for r in caplog.records
        if r.name.startswith(("httpx", "urllib3", "requests"))
    ]
    assert not http_records, f"model load hit the network: {http_records}"
