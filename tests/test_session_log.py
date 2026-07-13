"""Session logging tests using a temporary logs directory."""

import json
from datetime import datetime

from src.session_log import SessionLogger


def test_record_appends_jsonl_with_expected_fields(tmp_path):
    logger = SessionLogger(tmp_path)
    start = datetime(2026, 6, 30, 12, 0, 0)
    end = datetime(2026, 6, 30, 12, 0, 5)

    entry = logger.record(start, end, char_count=42, user="alice")

    assert entry == {
        "user": "alice",
        "start": "2026-06-30T12:00:00",
        "end": "2026-06-30T12:00:05",
        "duration_s": 5.0,
        "chars": 42,
    }

    lines = (tmp_path / "sessions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == entry


def test_records_are_appended_not_overwritten(tmp_path):
    logger = SessionLogger(tmp_path)
    t = datetime(2026, 6, 30, 12, 0, 0)
    logger.record(t, t, 1, user="a")
    logger.record(t, t, 2, user="b")

    lines = (tmp_path / "sessions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
