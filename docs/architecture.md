# Architecture

## Flow

```
hotkey DOWN ─▶ Controller.on_press ─▶ overlay.show_meter() ─▶ recorder.start()
hotkey UP   ─▶ (worker thread) Controller.on_release:
                 audio = recorder.stop()
                 overlay.show_text("… Transcribing")
                 text  = transcriber.transcribe(audio)
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
| tray | `pystray.Icon.run_detached` | `run()` blocks |
| keyboard | global hooks | provided by the `keyboard` library |
| worker | `Controller.on_release` | keep transcription off the hook thread |

The overlay is not mutated from worker/hook threads directly. They set a desired
mode (`meter` / `text` / `hidden`); a 40 ms `after` poll on the main thread
applies it and animates the level bars, keeping widget access single-threaded.

## Hotkey detection

`PushToTalk` registers `keyboard.add_hotkey(combo, on_press)` for the down edge
and `keyboard.on_release_key(trigger_key, on_release)` for the up edge, where
`trigger_key` is the last key of the combo (e.g. `shift` in `ctrl+shift`).

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

**Admin rights:** the `keyboard` library installs a low-level global hook that on
some Windows 11 setups requires running as administrator. If avoiding admin is a
hard requirement, swap `hotkey.py` to `pynput` keyboard listeners (tracking the
modifier+key set manually); the `PushToTalk` interface can stay the same.

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
