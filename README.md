# local_whisper_nemo

*[Deutsche Version](README_de.md)*

Portable push-to-talk dictation for Windows 11 and macOS, fully offline.

Hold `ctrl+shift`, speak, release — the text is typed straight into whatever
field has the cursor (Word, browser, chat, …). Speech recognition runs locally
with NVIDIA's [nemotron-3.5-asr-streaming-0.6b](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)
(40 locales, German and English included). Nothing leaves the machine.

## Install

**Windows** — double-click `install.bat`.
**macOS** — run `./install.sh`.

Either vendors `uv` and a portable Python into `tools/`, installs dependencies,
downloads the model into `models/`, and (Windows) puts a shortcut on the desktop.
No admin rights, no system Python.

## Run

**Windows** — double-click the desktop shortcut (or `run.bat`). The app sits in
the system tray.
**macOS** — run `./run.sh` from a terminal. There is no tray icon; quit with
Ctrl+C.

- **Hold** `ctrl+shift` → a small waveform indicator appears while recording.
- **Release** → the text is transcribed and typed at the cursor; the indicator disappears.
- **Quit** from the tray icon (Windows) or with Ctrl+C (macOS).

> **macOS permissions.** Grant the terminal you launch from *Microphone*,
> *Input Monitoring* and *Accessibility* under System Settings → Privacy &
> Security, then restart it. Without the last two the hotkey never fires or
> nothing gets typed — silently. See [docs/deployment.md](docs/deployment.md#macos-permissions).

> **Windows keyboard layouts.** If you have **more than one layout** installed,
> Windows uses `ctrl+shift` to switch between them. Set a different `HOTKEY` in
> `.env` (e.g. `ctrl+alt+space`) to avoid the clash.

Spoken formatting commands, German and English:

| say | you get |
|-----|---------|
| *new line* / *next line* / *neue Zeile* / *nächste Zeile* | line break |
| *new paragraph* / *neuer Absatz* | blank line between blocks |
| *tab* / *Tabulator* | tab stop |

The transcript is also cleaned up before it is typed: hesitations (*äh*, *ähm*,
*uh*, …) are dropped, and spelled-out numbers become digits — *dreiundzwanzig* →
`23`, *der dritte* → `der 3.`, *three point five* → `3.5`.

## Configure

Copy `.env.example` to `.env` and edit — model, language (`de-DE`, `en-US`, `auto`),
device (`cpu`/`cuda`), and hotkey. See [docs/configuration.md](docs/configuration.md).

## Develop

```
uv sync
uv run pytest -m "not slow"    # fast unit tests
uv run pytest -m slow          # loads the real model
uv run python -m src.main      # run from source
```

On macOS use `./install.sh` (or at least `scripts/bootstrap_python.sh`) rather
than a bare `uv sync`: it pins the in-folder uv-managed Python. Homebrew's
CPython is built without `_tkinter`, and the overlay will not import on it.

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the architecture.

## License

Apache-2.0. The ASR model is distributed by NVIDIA under OpenMDW-1.1.
