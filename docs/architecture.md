# Architecture

## Flow

```
hotkey DOWN ─▶ Controller.on_press ─▶ overlay.show_meter() ─▶ recorder.start()
hotkey UP   ─▶ (worker thread) Controller.on_release:
                 audio = recorder.stop()
                 overlay.show_text("… Transcribing")
                 text  = transcriber.transcribe(audio)
                 text  = postprocess.normalize(text, lang)  # fillers out, digits in
                 for kind, value in commands.parse(text):   # split text vs. keys
                     injector.inject/press(value)            # typed at cursor
                 logger.record(start, end, len(text))
                 overlay.hide()
```

`Controller` holds a `_busy` flag so a second press while recording, or a release
without a press, is ignored.

## Threads

| Thread | Runs | Why |
|--------|------|-----|
| main | Tk overlay `mainloop` | tkinter must own the main thread |
| tray | `pystray.Icon.run_detached` | `run()` blocks (Windows only — see below) |
| keyboard | global hooks | provided by the hotkey backend (`keyboard` / pynput) |
| worker | `Controller.on_release` | keep transcription off the hook thread |

The overlay is not mutated from worker/hook threads directly. They set a desired
mode (`meter` / `text` / `hidden`); a 40 ms `after` poll on the main thread
applies it and animates the level bars, keeping widget access single-threaded.

## Platform backends

Everything except keyboard input and text output is platform-neutral. The two
modules that are not select a backend at import:

| Module | Windows | macOS |
|--------|---------|-------|
| `injector.py` | `injector_win32` — Win32 `SendInput` | `injector_darwin` — pynput / Quartz |
| `hotkey.py` | `hotkey_keyboard` — `keyboard` global hooks | `hotkey_darwin` — pynput `Listener` |

Both backends of a module expose the same class (`TextInjector`, `PushToTalk`),
so `main.py` and `controller.py` never branch on the platform. The dependencies
split the same way: `keyboard` installs only on Windows and `pynput` only on
macOS, via `sys_platform` markers in `pyproject.toml`.

Unicode is handled equivalently on both sides — Win32 `KEYEVENTF_UNICODE` and
Quartz's Unicode event payload each carry the character itself rather than a key
code, so umlauts survive whatever keyboard layout is active.

The one feature that does not cross over is the **tray icon**. pystray builds its
macOS status item inside `run()`, which expects the main thread the Tk overlay
already owns; `run_detached()` there only marks the icon ready and creates
nothing. So `main.py` starts the tray on Windows only and prints a Ctrl+C quit
hint on macOS, rather than showing a menu that never appears.

## Hotkey detection

**Windows** (`hotkey_keyboard.py`) registers `keyboard.add_hotkey(combo, on_press)`
for the down edge and `keyboard.on_release_key(trigger_key, on_release)` for the
up edge, where `trigger_key` is the last key of the combo (e.g. `shift` in
`ctrl+shift`).

**macOS** (`hotkey_darwin.py`) has no press-and-hold primitive to build on, so it
watches raw key events through a pynput `Listener` and tracks which keys are
held: the held set covering the combo fires `start_cb`, releasing the trigger key
fires `stop_cb`. Events go through `Listener.canonical()` first, which collapses
left/right modifier variants and keeps a letter legible while modifiers are down.
`HOTKEY` takes the same spellings as on Windows, plus `cmd` and the aliases
`command` / `option` / `opt` / `control` / `super`.

**Why the default is a pure-modifier combo.** `ctrl+shift` holds down comfortably
for a long dictation and types nothing on its own if the app isn't running. The
`keyboard` library treats modifiers as ordinary keys, so `shift` is a valid
trigger key and no code change was needed. Two things to be aware of:

- Windows uses `ctrl+shift` to **switch keyboard layouts** when more than one
  layout is installed. If you have several, either remove the extra layouts or
  pick a different `HOTKEY` (e.g. `ctrl+alt+space`).
- Recording stops on release of the **last** key in the combo (`shift`). If you
  keep `ctrl` held down while the transcript is typed, the synthetic keystrokes
  arrive as `ctrl+<key>` shortcuts in the target app. In practice transcription
  takes ~1 s, by which time the modifiers are long released — but release the
  whole combo, not just `shift`.

**Permissions.** On Windows the `keyboard` library installs a low-level global
hook that on some Windows 11 setups requires running as administrator. macOS
gates the two halves separately through TCC, granted to whichever app launches
the process (Terminal, iTerm, …): the listener needs **Input Monitoring**, the
injector needs **Accessibility**. Missing either fails *silently* — no keys seen,
or nothing typed — rather than raising. If the Windows side ever needs to shed
its admin requirement, `hotkey_darwin.py` is a working pynput template.

## ASR model

`nvidia/nemotron-3.5-asr-streaming-0.6b` — a 600M-parameter multilingual RNN-T,
loaded through `transformers` (`AutoProcessor` + `AutoModelForRNNT`, requires
transformers ≥ 5.13). German is a first-tier locale (8.3 % WER); 40 locales total.

**Why offline mode, not streaming.** The model supports chunked streaming
decoding, but push-to-talk hands us the complete utterance on key release. One
`model.generate()` over the whole buffer is simpler and slightly more accurate —
streaming would only pay off if text had to appear *while* the user speaks, which
the PRD does not ask for. `processor(audio, language=…)` accepts a locale string
(`de-DE`) or `"auto"` for per-utterance language detection.

## Offline model storage

`Transcriber` passes `cache_dir=models/` to `from_pretrained`, so weights land
inside the app folder rather than the user's global HF cache. `download_model.py`
pre-fetches them during install, so runtime needs no network.

**Cache first, download only as a fallback.** `Transcriber.__init__` loads with
`local_files_only=True`; only if that raises `OSError` (empty or incomplete
cache) does it log a warning and retry with downloads enabled. So the normal
start is network-free, and a fresh checkout still works — it just pays the
~2.4 GB download once. `download_model.py` uses the same path: it is a plain
`Transcriber(settings)`, which downloads on a cold cache and is a fast local
load afterwards.

Why not simply always allow the network: without `local_files_only`,
`from_pretrained` revalidates every config file against the Hub on *each* start
(~25 HEAD requests: `config.json`, `processor_config.json`,
`tokenizer_config.json`, …). The weights still come from disk, so it is not a
re-download, but it leaks usage to the Hub and — the real problem — makes
startup hang on a bad connection: each of those requests waits out its own
connect timeout and retries, so a reachable-but-stalling network turns a 1 s
launch into minutes. `tests/test_transcriber.py` pins all three properties:
`test_importing_the_transcriber_puts_the_hub_client_offline`,
`test_model_loads_without_touching_the_network` (zero request logs during a
cached load) and `test_missing_cache_falls_back_to_download`.

**Why `local_files_only` alone is not enough.** The Hub client also makes calls
of its own: it fetches an agent-harness registry from the Hub at most once a
day, unrelated to the weights. It is best-effort telemetry, but on a connection
that accepts TCP and then stalls it burns its full 3 s timeout before startup
continues — and its `httpx` INFO line reads like a model download, which is how
this was first noticed (it is not: the weights load from disk in under a
second).

So `transcriber.py` sets `HF_HUB_OFFLINE=1` *before* importing `transformers`
(the constant is read once, at `huggingface_hub` import time). A cached start
then cannot make any request at all. `_download_and_load` lifts it again by
assigning `huggingface_hub.constants.HF_HUB_OFFLINE = False`, which the client
re-reads per call — so the fallback download still works.

Measured against a TCP blackhole endpoint with the registry cache cleared:

| load path | time |
|-----------|------|
| network-validating load (before `local_files_only`) | > 300 s, killed |
| cached load, `local_files_only` only | 3.8 s |
| cached load, offline at import | 1.0 s, zero requests attempted |

## Transcript cleanup

`postprocess.normalize(text, locale)` runs between the ASR and `commands.parse`,
because both fixes are easier on the raw sentence than on the split action plan —
and dropping hesitations first lets the number pass see "drei äh und zwanzig" as
the number it is.

**Hesitations.** A single regex removes `äh`, `ähm`, `ähem`, `öh(m)`, `hm`, `uh`,
`uhm`, `erm`, `umm` (repeated vowels/consonants included, so `ähhh` and `hmmm`
match). It eats the surrounding whitespace and commas too, so "Das ist, äh, ein
Test." becomes "Das ist ein Test." rather than leaving a doubled comma. If the
removal was at the very start, the new first letter is re-capitalised — "Ähm, das
war es." would otherwise start lowercase.

Two sounds are deliberately **not** in the list:

- `um` — the German preposition. The `", um … zu"` clause is comma-delimited
  exactly like the English filler, so no cheap rule separates them, and
  corrupting German sentences is worse than leaving an English "Um," in.
- `mhm` — an affirmation ("yes"), not a hesitation; removing it inverts meaning.

**Numbers.** `text_to_num.alpha2digit` (MIT) converts cardinals, ordinals and
decimals: `dreiundzwanzig` → `23`, `der dritte` → `der 3.`, `drei Komma fünf` →
`3,5`, `the third` → `the 3rd`, `three point five` → `3.5`. The decimal sign
follows the language, which is why the pass is language-specific.

The `threshold=1.5` argument is what keeps the indefinite article intact.
`alpha2digit` converts an *isolated* number only above the threshold, so `ein`
and `one` stay words while everything from two upwards converts:

| threshold | `ein Haus` | `zwei Punkte` | `dreiundzwanzig` |
|-----------|------------|---------------|------------------|
| 0 | `1 Haus` ✗ | `2 Punkte` | `23` |
| 1.5 | `ein Haus` | `2 Punkte` | `23` |
| 3.0 (library default) | `ein Haus` | `zwei Punkte` ✗ | `23` |

Grouped numbers, ordinals and decimals ignore the threshold entirely, so
"der erste Punkt" still becomes "der 1. Punkt".

**Language selection.** `ASR_LANGUAGE` picks the pass: `de-*` → German, `en-*` →
English, anything else (including `auto`) runs both. Running both is safe because
a pass only matches its own language's number words — German text through the
English pass, and vice versa, comes back byte-identical.
