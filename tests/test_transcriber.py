"""Transcriber tests.

The empty-input and fallback paths are fast and device-free. The real-model
paths are marked `slow` because they load the actual Nemotron model (from the
local cache).
"""

import logging
from dataclasses import replace

import huggingface_hub.constants
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


def test_importing_the_transcriber_puts_the_hub_client_offline():
    """A flaky connection must not be able to stall startup at all.

    huggingface_hub reads HF_HUB_OFFLINE at import time; importing `transcriber`
    has to have set it, or the Hub client is free to make its own calls (e.g. the
    daily agent-harness ping) that block on connect timeouts.
    """
    assert huggingface_hub.constants.HF_HUB_OFFLINE is True


def test_missing_cache_falls_back_to_download(tmp_path, monkeypatch, caplog):
    """An empty cache must lift offline mode and retry instead of failing."""
    attempts = []

    def fake_load(self, local_files_only):
        attempts.append((local_files_only, huggingface_hub.constants.HF_HUB_OFFLINE))
        if local_files_only:
            raise OSError("not in the disk cache")

    monkeypatch.setattr(Transcriber, "_load", fake_load)
    # setattr so the flipped constant is restored for the other tests.
    monkeypatch.setattr(huggingface_hub.constants, "HF_HUB_OFFLINE", True)
    settings = replace(load_settings(), models_dir=tmp_path / "models")

    with caplog.at_level(logging.WARNING):
        Transcriber(settings)

    # cached attempt stays offline; the retry runs with the network available
    assert attempts == [(True, True), (False, False)]
    assert "downloading" in caplog.text
