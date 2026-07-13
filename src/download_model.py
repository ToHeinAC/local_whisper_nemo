"""Pre-download the configured ASR model into the app's models/ folder.

Run once during installation so the app works fully offline afterwards.
"""

from __future__ import annotations

from .config import load_settings
from .transcriber import Transcriber


def main() -> None:
    settings = load_settings()
    print(f"Downloading model '{settings.model}' into {settings.models_dir} ...")
    # The only place allowed to reach the network; the app itself loads from cache.
    Transcriber(settings, allow_download=True)
    print("Model downloaded.")


if __name__ == "__main__":
    main()
