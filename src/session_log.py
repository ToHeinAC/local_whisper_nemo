"""Append-only per-session logging.

Each completed dictation appends one JSON object (JSONL) to
`logs/sessions.jsonl`, capturing the Windows account user and timing so sessions
are easy to monitor.
"""

from __future__ import annotations

import getpass
import json
from datetime import datetime
from pathlib import Path


class SessionLogger:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.logs_dir / "sessions.jsonl"

    def record(
        self,
        start: datetime,
        end: datetime,
        char_count: int,
        user: str | None = None,
    ) -> dict:
        """Append a session record and return it."""
        entry = {
            "user": user if user is not None else getpass.getuser(),
            "start": start.isoformat(timespec="seconds"),
            "end": end.isoformat(timespec="seconds"),
            "duration_s": round((end - start).total_seconds(), 2),
            "chars": char_count,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
