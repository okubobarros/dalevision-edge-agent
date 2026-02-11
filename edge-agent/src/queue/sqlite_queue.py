import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Dict, Any


class SqliteQueue:
    def __init__(self, path: str):
        self.path = str(path)
        Path(os.path.dirname(self.path)).mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def enqueue(self, item: Dict[str, Any]) -> None:
        payload = json.dumps(item, ensure_ascii=False)
        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO queue (payload, created_at) VALUES (?, ?)",
                (payload, created_at),
            )
            self._conn.commit()

    def dequeue_batch(self, limit: int = 50) -> List[Tuple[int, Dict[str, Any]]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, payload FROM queue ORDER BY id ASC LIMIT ?",
                (int(limit),),
            )
            rows = cur.fetchall()
        out: List[Tuple[int, Dict[str, Any]]] = []
        for row_id, payload in rows:
            try:
                data = json.loads(payload)
            except Exception:
                data = {}
            out.append((int(row_id), data))
        return out

    def ack(self, row_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM queue WHERE id = ?", (int(row_id),))
            self._conn.commit()

    def size(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(1) FROM queue")
            row = cur.fetchone()
            return int(row[0]) if row else 0
