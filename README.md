# local_whisper_nemo

*[Deutsche Version](README_de.md)*

Portable Windows 11 push-to-talk dictation, fully offline.

Hold `ctrl+shift`, speak, release — the text is typed straight into whatever
field has the cursor (Word, browser, chat, …). Speech recognition runs locally
with NVIDIA's [nemotron-3.5-asr-streaming-0.6b](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)
(40 locales, German and English included). Nothing leaves the machine.

## Install

Double-click `install.bat`. It vendors `uv` and a portable Python into `tools\`,
installs dependencies, downloads the model into `models\`, and puts a shortcut on
the desktop. No admin rights, no system Python.

## Run

Double-click the desktop shortcut (or `run.bat`). The app sits in the system tray.

- **Hold** `ctrl+shift` → a small waveform indicator appears while recording.
- **Release** → the text is transcribed and typed at the cursor; the indicator disappears.
- **Quit** from the tray icon.

> If you have **more than one keyboard layout** installed, Windows uses
> `ctrl+shift` to switch between them. Set a different `HOTKEY` in `.env`
> (e.g. `ctrl+alt+space`) to avoid the clash.

Spoken formatting commands: *new line*, *next line*, *new paragraph*, *tab*.

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

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the architecture.

## License

Apache-2.0. The ASR model is distributed by NVIDIA under OpenMDW-1.1.
