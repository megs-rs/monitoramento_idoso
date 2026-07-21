from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from monitoramento_idoso.events.models import Event

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    camera_ip TEXT NOT NULL,
    event_type TEXT NOT NULL,
    clip_path TEXT DEFAULT ''
);
"""


class EventDatabase:
    def __init__(self, db_path: Path | str = "data/events.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute(_SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def insert(self, event: Event) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO events (timestamp, camera_ip, event_type, clip_path) "
            "VALUES (?, ?, ?, ?)",
            (
                event.timestamp.isoformat() if event.timestamp else datetime.now().isoformat(),
                event.camera_ip,
                event.event_type,
                event.clip_path,
            ),
        )
        conn.commit()
        event_id = cursor.lastrowid
        logger.info("Event logged: id=%d type=%s camera=%s", event_id, event.event_type, event.camera_ip)
        return event_id

    def list_recent(self, limit: int = 50) -> list[Event]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            Event(
                id=row["id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                camera_ip=row["camera_ip"],
                event_type=row["event_type"],
                clip_path=row["clip_path"],
            )
            for row in rows
        ]
