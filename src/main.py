"""Entry point: wire everything together and run.

Threading model:
- main thread runs the Tk overlay mainloop
- the tray icon runs on its own thread (run_detached)
- keyboard hooks fire on the keyboard library's thread; the stop handler offloads
  transcription to a worker thread so the hook returns immediately
"""

from __future__ import annotations

import logging
import threading

from .config import load_settings
from .controller import Controller
from .hotkey import PushToTalk
from .injector import TextInjector
from .overlay import Overlay
from .recorder import AudioRecorder
from .session_log import SessionLogger
from .transcriber import Transcriber
from .tray import create_tray


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()

    print(f"Loading ASR model '{settings.model}' ({settings.device})...")
    transcriber = Transcriber(settings)
    print("Model ready.")

    recorder = AudioRecorder(settings.sample_rate)
    overlay = Overlay(level_source=recorder.level)
    controller = Controller(
        recorder=recorder,
        transcriber=transcriber,
        injector=TextInjector(settings.type_delay),
        logger=SessionLogger(settings.logs_dir),
        overlay=overlay,
    )

    def stop_in_worker() -> None:
        threading.Thread(target=controller.on_release, daemon=True).start()

    ptt = PushToTalk(settings.hotkey, controller.on_press, stop_in_worker)
    try:
        ptt.start()
    except ValueError as exc:
        print(
            f"\nInvalid HOTKEY {settings.hotkey!r} in .env: {exc.args[0]}\n"
            "Use keyboard-library key names, e.g. 'ctrl+alt+space'."
        )
        raise SystemExit(1)

    tray = create_tray(on_quit=overlay.stop)
    tray.run_detached()

    print(f"Ready. Hold {settings.hotkey} to dictate. Quit from the tray icon.")
    overlay.mainloop()


if __name__ == "__main__":
    main()
