"""Entry point: wire everything together and run.

Threading model:
- main thread runs the Tk overlay mainloop
- the tray icon runs on its own thread (run_detached); Windows only
- keyboard hooks fire on the hotkey backend's thread; the stop handler offloads
  transcription to a worker thread so the hook returns immediately
"""

from __future__ import annotations

import logging
import sys
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

    print(
        f"Loading ASR model '{settings.model}' ({settings.device}) "
        f"from {settings.models_dir} ..."
    )
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
        language=settings.language,
    )

    def stop_in_worker() -> None:
        threading.Thread(target=controller.on_release, daemon=True).start()

    ptt = PushToTalk(settings.hotkey, controller.on_press, stop_in_worker)
    try:
        ptt.start()
    except ValueError as exc:
        print(
            f"\nInvalid HOTKEY {settings.hotkey!r} in .env: {exc.args[0]}\n"
            "Use key names like 'ctrl+shift' or 'ctrl+alt+space'."
        )
        raise SystemExit(1)

    if sys.platform == "darwin":
        # pystray builds its macOS status item inside run(), which wants the main
        # thread the Tk overlay already owns; run_detached() there only marks the
        # icon ready and shows nothing. Skip it rather than pretend it is there.
        quit_hint = "Quit with Ctrl+C."
    else:
        create_tray(on_quit=overlay.stop).run_detached()
        quit_hint = "Quit from the tray icon."

    print(f"Ready. Hold {settings.hotkey} to dictate. {quit_hint}")
    try:
        overlay.mainloop()
    except KeyboardInterrupt:
        overlay.stop()


if __name__ == "__main__":
    main()
