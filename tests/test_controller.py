"""Controller state-machine tests with mocked components."""

from unittest.mock import MagicMock

import numpy as np

from src.controller import Controller


def _make_controller(text="hello world"):
    recorder = MagicMock()
    recorder.stop.return_value = np.zeros(10, dtype=np.float32)
    transcriber = MagicMock()
    transcriber.transcribe.return_value = text
    injector = MagicMock()
    logger = MagicMock()
    overlay = MagicMock()
    ctrl = Controller(recorder, transcriber, injector, logger, overlay)
    return ctrl, recorder, transcriber, injector, logger, overlay


def test_full_cycle_records_transcribes_injects_and_logs():
    ctrl, recorder, transcriber, injector, logger, overlay = _make_controller()

    ctrl.on_press()
    recorder.start.assert_called_once()

    ctrl.on_release()
    recorder.stop.assert_called_once()
    transcriber.transcribe.assert_called_once()
    injector.inject.assert_called_once_with("hello world")
    logger.record.assert_called_once()
    overlay.hide.assert_called_once()


def test_empty_transcript_is_not_injected_but_still_logged():
    ctrl, _r, _t, injector, logger, _o = _make_controller(text="")
    ctrl.on_press()
    ctrl.on_release()
    injector.inject.assert_not_called()
    logger.record.assert_called_once()


def test_release_without_press_is_ignored():
    ctrl, recorder, _t, _i, logger, _o = _make_controller()
    ctrl.on_release()
    recorder.stop.assert_not_called()
    logger.record.assert_not_called()


def test_second_press_while_busy_is_ignored():
    ctrl, recorder, _t, _i, _l, _o = _make_controller()
    ctrl.on_press()
    ctrl.on_press()
    assert recorder.start.call_count == 1
