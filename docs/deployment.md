# Deployment

The app deploys as a self-contained folder: code, the uv-managed virtual
environment, the model weights, and logs all live together.

## Prerequisites

- Windows 11, or macOS (Apple silicon or Intel)
- Network access **for the one-time install only**

No admin rights, no pre-installed tooling, and **no system Python** are required.
The installer bootstraps its own portable [uv](https://docs.astral.sh/uv/) into
`tools/` (a single static binary, no installer/registry), then has uv download a
managed CPython **into the folder** at `tools/python` (via
`UV_PYTHON_INSTALL_DIR`). Both the tool and the interpreter live under `tools/`,
so the deployed folder is self-contained.

|  | Windows | macOS |
|--|---------|-------|
| install | `install.bat` | `./install.sh` |
| run | `run.bat` or the desktop shortcut | `./run.sh` |
| bootstrap scripts | `scripts\*.ps1` | `scripts/*.sh` |

## Install (once)

```bat
install.bat
```
```bash
./install.sh
```

Either will:
1. create `.env` from `.env.example` (if missing),
2. **bootstrap `uv`** — `scripts\bootstrap_uv.ps1` / `scripts/bootstrap_uv.sh`
   downloads the portable uv binary into `tools\` (reuses a PATH `uv` if one
   exists; no-op if already vendored),
3. **bootstrap Python** — `scripts\bootstrap_python.ps1` / `bootstrap_python.sh`
   has uv install a managed CPython (pinned by `.python-version`) into
   `tools\python` (no-op if present), and removes any `.venv` copied from another
   machine whose interpreter path is now dead, so step 4 rebuilds it cleanly,
4. `uv sync` — create `.venv/` (against the in-folder Python) and install
   dependencies (torch + transformers: ~1 GB, this is the slow step),
5. download the Nemotron ASR weights into `models/` (~2.4 GB incl. the HF cache
   layout; skipped if they are already there),
6. **Windows only:** create a **desktop shortcut** (`local_whisper_nemo.lnk`,
   launches minimized). macOS has no single-file equivalent — add `run.sh` to
   System Settings → General → Login Items, or copy it to `run.command` to make
   it double-clickable in Finder.

The install and run scripts of both platforms set `UV_PYTHON_INSTALL_DIR` to
`tools\python` and resolve `uv` from `tools\uv.exe` / `tools/uv` first, falling
back to a `uv` on PATH. The run script downloads nothing as long as `models/`
holds the weights - if it doesn't, the app fetches them once (logged as a
warning) instead of failing. If `uv` is missing it tells you to run the
installer.

## Run

- Windows: double-click the desktop shortcut, or run `run.bat`.
  macOS: `./run.sh` from a terminal.
- Startup loads the model into RAM (~45 s on CPU) before the hotkey works.
- Hold the hotkey (`ctrl+shift`), speak, release — text appears at the cursor.
- Quit from the tray icon (red dot) → **Quit** on Windows; with Ctrl+C in the
  launching terminal on macOS.

> **Windows 11 tray:** new tray icons are hidden in the overflow flyout by
> default. Click the `^` chevron next to the clock to find the red dot, or pin it
> via Settings → Personalization → Taskbar → Other system tray icons.

If global hotkeys don't fire on Windows, run `run.bat` as administrator (see
[architecture.md](architecture.md) on the `keyboard` hook).

### macOS permissions

macOS gates microphone and keyboard access per app, and the app being gated is
the **terminal you launch from** (Terminal, iTerm, VS Code …), not Python. Grant
all three under System Settings → Privacy & Security:

| Permission | Needed for | Symptom if missing |
|------------|-----------|--------------------|
| Microphone | `recorder.py` | prompted on first dictation; empty audio if denied |
| Input Monitoring | the pynput hotkey listener | the hotkey never fires |
| Accessibility | the pynput text injector | recording works, nothing is typed |

Only the microphone prompts on its own; the other two fail silently, so set them
before the first run. After granting Input Monitoring or Accessibility, **restart
the terminal app** — macOS only re-reads them at process start.

**There is no tray icon on macOS.** pystray builds its status item inside
`run()`, which wants the main thread the Tk overlay already owns, and its
detached mode on macOS shows nothing at all — so the app skips it and says so at
startup (`Quit with Ctrl+C.`). The recording overlay is unaffected.

## Moving to another machine

Copy the whole folder and run the installer once on the target (needs no system
Python — it uses the vendored `tools\uv.exe` + `tools\python`, needing network
only to `uv sync` deps and fetch the model if they aren't already cached).
`tools/` and `.venv/` are platform-specific: a folder carried from Windows to
macOS re-bootstraps both, while `models/` carries over as-is.

A copied `.venv/` cannot just be reused as-is: `pyvenv.cfg` records the **absolute**
path of the Python that built it, which won't match the new machine/location. The
install step detects that stale `.venv` and rebuilds it against `tools\python`, so
you don't hit a dead-interpreter error.

## Logs

`logs/sessions.jsonl` — one JSON object per dictation:

```json
{"user":"he","start":"2026-07-13T12:00:00","end":"2026-07-13T12:00:05","duration_s":5.0,"chars":42}
```
