"""Application configuration loaded from environment / .env.

All paths resolve relative to the application root so the whole folder stays
portable: dependencies, models and logs live next to the code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import torch
from dotenv import load_dotenv

# Application root = parent of this `src/` package.
APP_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = APP_ROOT / "models"
LOGS_DIR = APP_ROOT / "logs"


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings."""

    model: str
    language: str  # locale like "de-DE", or "auto" to detect per utterance
    device: str  # "cpu" or "cuda"
    hotkey: str
    type_delay: float
    sample_rate: int
    models_dir: Path
    logs_dir: Path


def _resolve_device(value: str) -> str:
    """Map the DEVICE setting to a concrete torch device."""
    if value == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return value


def load_settings() -> Settings:
    """Read .env (if present) and the environment into a Settings object."""
    load_dotenv(APP_ROOT / ".env")

    return Settings(
        model=os.getenv("ASR_MODEL", "nvidia/nemotron-3.5-asr-streaming-0.6b").strip(),
        language=os.getenv("ASR_LANGUAGE", "auto").strip(),
        device=_resolve_device(os.getenv("DEVICE", "auto").strip().lower()),
        hotkey=os.getenv("HOTKEY", "ctrl+shift").strip(),
        type_delay=float(os.getenv("TYPE_DELAY", "0.0")),
        sample_rate=int(os.getenv("SAMPLE_RATE", "16000")),
        models_dir=MODELS_DIR,
        logs_dir=LOGS_DIR,
    )
