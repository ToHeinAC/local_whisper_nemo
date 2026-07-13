"""Nemotron ASR wrapper (transformers).

The model is loaded once and reused. Weights are cached under the app's
`models/` folder so the whole application stays self-contained and offline.

Although `nemotron-3.5-asr-streaming-0.6b` is a streaming model, push-to-talk
hands us the complete utterance on key release, so we transcribe the whole
buffer in one offline `generate()` call — simpler and more accurate than
driving the chunked streaming API for text nobody sees until the end.
"""

from __future__ import annotations

import numpy as np
import torch
from transformers import AutoModelForRNNT, AutoProcessor

from .config import Settings


class Transcriber:
    def __init__(self, settings: Settings, allow_download: bool = False) -> None:
        """Load the model. Reads only the local cache unless `allow_download`.

        Without `local_files_only`, `from_pretrained` revalidates every config
        file against the Hub on each start: a dozen HEAD requests that make
        startup slower and dependent on network reachability, even though the
        weights are already on disk. Only `download_model.py` needs the network.
        """
        self._settings = settings
        settings.models_dir.mkdir(parents=True, exist_ok=True)
        load_args = {
            "cache_dir": str(settings.models_dir),
            "local_files_only": not allow_download,
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
