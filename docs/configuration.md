# Configuration

All settings are read from `.env` (copy from `.env.example`). Loaded by
`src/config.py` into a frozen `Settings` dataclass.

| Variable | Default | Meaning |
|----------|---------|---------|
| `ASR_MODEL` | `nvidia/nemotron-3.5-asr-streaming-0.6b` | Hugging Face model id |
| `ASR_LANGUAGE` | `auto` | Locale (`de-DE`, `en-US`, …) or `auto` to detect per utterance |
| `DEVICE` | `auto` | `auto` (CUDA if available), `cpu`, or `cuda` |
| `HOTKEY` | `ctrl+shift` | Push-to-talk combo (`keyboard` library syntax) |
| `TYPE_DELAY` | `0.0` | Seconds between simulated keystrokes |
| `SAMPLE_RATE` | `16000` | Mic capture rate (Hz); the model expects 16000 |

## Paths

Resolved relative to the application root (parent of `src/`), keeping the folder
portable:

- `models/` — Hugging Face cache for the ASR weights (`cache_dir`)
- `logs/sessions.jsonl` — appended session records

## Hotkey

Recording starts when the whole combo is down and stops when the **last** key in
it is released — so `HOTKEY=ctrl+shift` stops on release of `shift`. Pure-modifier
combos are allowed; so are classic ones like `ctrl+alt+space`.

Change the default if you have **more than one keyboard layout installed**:
Windows itself uses `ctrl+shift` to cycle layouts, and it will keep doing so.
See [architecture.md](architecture.md#hotkey-detection) for the full caveats.

## Accuracy / speed trade-offs

- Pin `ASR_LANGUAGE=de-DE` if you only dictate German: it skips language
  detection and avoids the model switching locale mid-utterance.
- `DEVICE=auto` picks CUDA when a GPU is present (fp16) and CPU otherwise (fp32).
  The 0.6B model is small enough to run on CPU faster than real time.
- Transcription-ready locales include `de-DE`, `en-US`, `en-GB`, `fr-FR`, `es-ES`,
  `it-IT`, `nl-NL`, `pt-PT`, `pl-PL` and more — see the model card for the full list.
