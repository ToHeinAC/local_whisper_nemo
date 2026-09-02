"""Nemotron ASR wrapper (transformers).

The model is loaded once and reused. Weights are cached under the app's
`models/` folder so the whole application stays self-contained and offline;
the cache is downloaded once on first use and never consulted over the network
again.

Although `nemotron-3.5-asr-streaming-0.6b` is a streaming model, push-to-talk
hands us the complete utterance on key release, so we transcribe the whole
buffer in one offline `generate()` call — simpler and more accurate than
driving the chunked streaming API for text nobody sees until the end.
"""

from __future__ import annotations

import logging
import os

# Start the process offline. `huggingface_hub` reads HF_HUB_OFFLINE once, at
# import time, so this has to happen before `transformers` is imported. It makes
# a cached load provably network-free: not just the weights, but also the
# once-a-day agent-harness ping the Hub client makes on its own. On a flaky
# connection those calls block on connect timeouts and retries, which is what
# made startup crawl. `_download_and_load` lifts the flag when the cache is empty.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import huggingface_hub.constants  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from transformers import AutoModelForRNNT, AutoProcessor  # noqa: E402

from .config import Settings  # noqa: E402

log = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, settings: Settings) -> None:
        """Load from the local cache, downloading only when it is not there.

        The cached load passes `local_files_only=True`: without it,
        `from_pretrained` revalidates every config file against the Hub on each
        start — a dozen HEAD requests that make startup slower and dependent on
        network reachability, even though the weights are already on disk.
        """
        self._settings = settings
        settings.models_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._load(local_files_only=True)
        except OSError:
            self._download_and_load()

    def _download_and_load(self) -> None:
        """Re-enable the network and fetch the model — the cache was unusable."""
        log.warning(
            "Model %r not found in %s - downloading it once (needs internet).",
            self._settings.model,
            self._settings.models_dir,
        )
        # Read at call time by the Hub client, so flipping it here is enough to
        # undo the module-level HF_HUB_OFFLINE for the rest of the process.
        huggingface_hub.constants.HF_HUB_OFFLINE = False
        self._load(local_files_only=False)

    def _load(self, local_files_only: bool) -> None:
        settings = self._settings
        load_args = {
            "cache_dir": str(settings.models_dir),
            "local_files_only": local_files_only,
        }
        self._processor = AutoProcessor.from_pretrained(settings.model, **load_args)
        self._model = AutoModelForRNNT.from_pretrained(
            settings.model,
            dtype=torch.float16 if settings.device == "cuda" else torch.float32,
            **load_args,
        ).to(settings.device)
        self._model.eval()

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe mono float32 audio into stripped text."""
        if audio.size == 0:
            return ""
        inputs = self._processor(
            audio,
            sampling_rate=self._settings.sample_rate,
            language=self._settings.language,
            return_tensors="pt",
        ).to(self._model.device, dtype=self._model.dtype)

        with torch.inference_mode():
            output = self._model.generate(**inputs, return_dict_in_generate=True)

        decoded = self._processor.decode(output.sequences, skip_special_tokens=True)
        if isinstance(decoded, list):  # batched decode returns one string per sequence
            decoded = " ".join(decoded)
        return decoded.strip()
