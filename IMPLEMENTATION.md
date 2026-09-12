# IMPLEMENTATION.md

Current implementation state of **local_whisper_nemo**. See [PRD.md](PRD.md) for the
original goals and [docs/](docs/) for component detail.

> Note: the CLAUDE.md tech section mentions an LLM `prompts.py`. That is template
> boilerplate and does **not** apply here — this is a background tray app with no
> web UI and no LLM prompting. No `src/prompts.py` exists.

## What it does

Hold a global hotkey (`ctrl+shift` by default) → record the microphone →
transcribe locally with NVIDIA Nemotron ASR → type the text at the cursor →
release hides the indicator and logs the session. Fully offline; model weights
live in `models/`. Runs on **Windows 11 and macOS** — keyboard capture and text
injection have a backend per platform, everything else is shared.

**Voice formatting commands** (recognised in the transcript by `commands.py`),
German and English:

| spoken | effect |
|--------|--------|
| `new line` / `next line` / `neue Zeile` / `nächste Zeile` | Enter |
| `new paragraph` / `neuer Absatz` | Enter×2 (blank line between blocks) |
| `tab` / `Tabulator` | Tab |

The match eats whitespace/punctuation the model puts around the spoken command,
so a punctuation mark dictated right next to a command word may be swallowed.

**Transcript cleanup** (`postprocess.py`, runs before `commands.parse`):
hesitations (`äh`, `ähm`, `hm`, `uh`, `erm`, …) are dropped together with the
commas the ASR sets them off with, and spelled-out numbers become digits —
cardinals, ordinals and decimals, in both languages (`dreiundzwanzig` → `23`,
`der dritte` → `der 3.`, `drei Komma fünf` → `3,5`). Details and the two
deliberate exclusions are in
[docs/architecture.md](docs/architecture.md#transcript-cleanup).

## Components (`src/`)

| Module | Responsibility |
|--------|----------------|
| `config.py` | Load `.env` into a `Settings` dataclass; resolve app-relative paths and the torch device |
| `recorder.py` | `AudioRecorder` — mic capture (sounddevice) → mono float32 numpy |
| `transcriber.py` | `Transcriber` — Nemotron ASR via transformers; forces the Hub client offline and loads from the `models/` cache, downloading only if it is missing |
| `postprocess.py` | `normalize()` — drop hesitations, spell numbers as digits (de/en) |
| `commands.py` | `parse()` — split transcript into text + special-key actions (voice formatting) |
| `injector.py` | picks the `TextInjector` backend: `injector_win32.py` (Win32 `SendInput`) or `injector_darwin.py` (pynput/Quartz) — both type text (`inject`) and press keys (`press`) at the cursor |
| `overlay.py` | `Overlay` — status indicator: animated mic-level waveform while recording, text while transcribing (tkinter). On macOS it also takes the process out of the activation order, so showing it does not steal the focus the injected text depends on |
| `tray.py` | system-tray icon with Quit (pystray); Windows only |
| `session_log.py` | `SessionLogger` — append JSONL session records |
| `hotkey.py` | picks the `PushToTalk` backend: `hotkey_keyboard.py` (`keyboard` hooks) or `hotkey_darwin.py` (pynput `Listener` + held-key set) — both are global press/release listeners |
| `controller.py` | `Controller` — record→transcribe→inject→log state machine |
| `main.py` | wiring + threading + run loop |
| `download_model.py` | one-time model pre-download for offline use |

`config.py`, `transcriber.py`, `postprocess.py` and `download_model.py` are new
relative to [local_whisper](https://github.com/ToHeinAC/local_whisper) (the ASR
engine is the substantive difference); `injector.py` and `hotkey.py` gained the
macOS backends. The rest is carried over unchanged. Backend selection lives in
those two modules alone — no other module branches on the platform. See
[docs/architecture.md](docs/architecture.md#platform-backends).

## Model

`nvidia/nemotron-3.5-asr-streaming-0.6b` (OpenMDW-1.1), loaded with
`AutoProcessor` + `AutoModelForRNNT` (transformers ≥ 5.13). Despite being a
streaming model it is used in **offline mode**: push-to-talk delivers the whole
utterance on key release, so one `generate()` over the full buffer is simpler and
more accurate than driving the chunked streaming API. Rationale and the
language-code handling are in [docs/architecture.md](docs/architecture.md).

Measured on CPU (fp32): 11 s of speech transcribed in ~1.5 s; first model load
~45 s.

`transcriber.py` sets `HF_HUB_OFFLINE=1` before importing `transformers` and
loads with `local_files_only=True`, so a normal start makes **zero** HTTP
requests and cannot stall on a bad connection — weights and configs come from
`models/` only. If that cache is missing, the load logs a warning, lifts offline
mode and retries with downloads enabled; `download_model.py` relies on the same
path during install. See
[docs/architecture.md](docs/architecture.md#offline-model-storage).

## Threading model

- Main thread: Tk overlay `mainloop`.
- Tray icon: own thread via `run_detached` — Windows only; `main.py` skips it on
  macOS, where pystray's detached mode shows nothing.
- Keyboard hooks: the hotkey backend's own thread (`keyboard` / pynput
  `Listener`); the release handler offloads transcription to a worker thread so
  the hook returns immediately.
- Overlay is updated thread-safely (other threads set desired state; a 40 ms
  poll on the main thread applies it).

## Configuration

All settings come from `.env` (see `.env.example`). Details in
[docs/configuration.md](docs/configuration.md).

## Run & deploy

Windows: `install.bat` (vendor uv + Python into `tools\`, sync deps, download
model, desktop shortcut), then `run.bat`.
macOS: `./install.sh`, then `./run.sh` — same steps, no shortcut, and the
launching terminal needs the Microphone, **Input Monitoring** and
**Accessibility** permissions.
No system Python required on either. Details in
[docs/deployment.md](docs/deployment.md).

## Tests

`uv run pytest -m "not slow"` — 55 fast unit tests (hardware mocked); the
platform backends account for the skips, 1 on macOS and 8 on Windows.
`uv run pytest -m slow` — integration test that loads the real model.

| Area | Test file |
|------|-----------|
| recorder buffer / level meter | `tests/test_recorder.py` |
| transcriber (empty + real model) | `tests/test_transcriber.py` |
| voice formatting commands | `tests/test_commands.py` |
| text injection | `tests/test_injector.py` |
| hotkey combo parsing + hold/release (macOS) | `tests/test_hotkey.py` |
| overlay level scaling | `tests/test_overlay.py` |
| session logging | `tests/test_session_log.py` |
| controller state machine | `tests/test_controller.py` |

## Known constraints / open items

- The `keyboard` library global hook may require running as **administrator** on
  Windows 11. `hotkey_darwin.py` is a working pynput template if that has to go.
- macOS, verified end-to-end against a real TextEdit window: a full
  record→transcribe→inject cycle (audio and ASR mocked) types `Grüße ABC` at the
  cursor with umlauts intact, and Tk starts from inside the `.venv`. The overlay
  must neither activate the process nor re-order its window — both were needed,
  see [docs/architecture.md](docs/architecture.md#platform-backends).
- macOS, still unverified: the live hotkey and its Input Monitoring prompt (a
  global listener cannot be exercised from a test session), and whether the
  overlay actually *renders* — checking pixels needs Screen Recording
  permission, which the development session did not have.
- No tray icon on macOS: pystray creates its status item only inside `run()`,
   which needs the main thread the Tk overlay owns. Quit is Ctrl+C there.
- On Apple silicon `DEVICE=auto` resolves to `cpu`. `DEVICE=mps` is passed
  through to torch untouched but has not been verified for this RNN-T.
- The `ctrl+shift` default is **not yet confirmed on a live desktop**: global
  hooks cannot be exercised from a headless test session (even the previous
  `ctrl+alt+space` default produces no callbacks there), so this needs a manual
  check. It also collides with Windows' own layout-switch shortcut when multiple
  keyboard layouts are installed. See docs/architecture.md.
- `librosa` is a hard runtime dependency of the model's feature extractor (not
  mentioned on the model card, discovered at first load).
- Manual verification still pending: real hold-to-talk typing into Notepad/Word,
  umlaut fidelity, tray + overlay behavior on the live desktop.
- German accuracy not yet measured on real dictation (model card: 8.31 % WER).
