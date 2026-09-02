"""Pre-download the configured ASR model into the app's models/ folder.

Run once during installation so the app works fully offline afterwards.
"""

from __future__ import annotations

from .config import load_settings
from .transcriber import Transcriber


def main() -> None:
    settings = load_settings()
    print(f"Ensuring model '{settings.model}' is in {settings.models_dir} ...")
    # Downloads only if the cache is empty; a second run is a no-op local load.
    Transcriber(settings)
    print("Model ready.")


if __name__ == "__main__":
    main()
