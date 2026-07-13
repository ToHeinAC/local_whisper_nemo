# Deployment

The app deploys as a self-contained folder: code, the uv-managed virtual
environment, the model weights, and logs all live together.

## Prerequisites

- Windows 11
- Network access **for the one-time install only**

No admin rights, no pre-installed tooling, and **no system Python** are required.
`install.bat` bootstraps its own portable [uv](https://docs.astral.sh/uv/) into
`tools\uv.exe` (a single static binary, no installer/registry), then has uv
download a managed CPython **into the folder** at `tools\python` (via
`UV_PYTHON_INSTALL_DIR`). Both the tool and the interpreter live under `tools\`,
so the deployed folder is self-contained.

## Install (once)

```bat
install.bat
```

This will:
1. create `.env` from `.env.example` (if missing),
2. **bootstrap `uv`** — `scripts\bootstrap_uv.ps1` downloads the portable
   `uv.exe` into `tools\` (reuses a PATH `uv` if one exists; no-op if already
   vendored),
3. **bootstrap Python** — `scripts\bootstrap_python.ps1` has uv install a managed
   CPython (pinned by `.python-version`) into `tools\python` (no-op if present),
   and removes any `.venv` copied from another machine whose interpreter path is
   now dead, so step 4 rebuilds it cleanly,
4. `uv sync` — create `.venv/` (against the in-folder Python) and install
   dependencies (torch + transformers: ~1 GB, this is the slow step),
5. download the Nemotron ASR weights into `models/` (~2.4 GB incl. the HF cache
   layout),
6. create a **desktop shortcut** (`local_whisper_nemo.lnk`, launches minimized).

Both `install.bat` and `run.bat` set `UV_PYTHON_INSTALL_DIR` to `tools\python` and
resolve `uv` from `tools\uv.exe` first, falling back to a `uv` on PATH. `run.bat`
never downloads anything; if `uv` is missing it tells you to run `install.bat`.

## Run

- Double-click the desktop shortcut, or run `run.bat`.
- Startup loads the model into RAM (~45 s on CPU) before the hotkey works.
- Hold the hotkey (`ctrl+alt+space`), speak, release — text appears at the cursor.
- Quit from the tray icon (red dot) → **Quit**.

> **Windows 11 tray:** new tray icons are hidden in the overflow flyout by
> default. Click the `^` chevron next to the clock to find the red dot, or pin it
> via Settings → Personalization → Taskbar → Other system tray icons.

If global hotkeys don't fire, run `run.bat` as administrator (see
[architecture.md](architecture.md) on the `keyboard` hook).

## Moving to another machine

Copy the whole folder and run `install.bat` once on the target (needs no system
Python — it uses the vendored `tools\uv.exe` + `tools\python`, needing network
only to `uv sync` deps and fetch the model if they aren't already cached).

A copied `.venv/` cannot just be reused as-is: `pyvenv.cfg` records the **absolute**
path of the Python that built it, which won't match the new machine/location. The
install step detects that stale `.venv` and rebuilds it against `tools\python`, so
you don't hit a dead-interpreter error.

## Logs

`logs/sessions.jsonl` — one JSON object per dictation:

```json
{"user":"he","start":"2026-07-13T12:00:00","end":"2026-07-13T12:00:05","duration_s":5.0,"chars":42}
```
