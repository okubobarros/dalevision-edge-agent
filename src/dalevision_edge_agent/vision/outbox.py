from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


class VisionOutbox:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT UNIQUE,
                    payload_json TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at REAL NOT NULL,
                    next_attempt_at REAL NOT NULL DEFAULT 0
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_outbox_next_attempt ON outbox(next_attempt_at)"
            )
            self._conn.commit()

    def enqueue(self, payload: Dict[str, Any]) -> bool:
        receipt_id = str(payload.get("receipt_id") or "").strip()
        if not receipt_id:
            return False
        payload_json = json.dumps(payload, ensure_ascii=False)
        now = time.time()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT OR IGNORE INTO outbox
                (receipt_id, payload_json, created_at, next_attempt_at)
                VALUES (?, ?, ?, 0)
                """,
                (receipt_id, payload_json, now),
            )
            self._conn.commit()
            return cur.rowcount == 1

    def peek_batch(self, limit: int = 50) -> List[Tuple[int, Dict[str, Any], int]]:
        now = time.time()
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, payload_json, attempts
                FROM outbox
                WHERE next_attempt_at <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (now, int(limit)),
            ).fetchall()

        out: List[Tuple[int, Dict[str, Any], int]] = []
        for row in rows:
            try:
                payload = json.loads(row["payload_json"])
            except Exception:
                payload = {}
            out.append((int(row["id"]), payload, int(row["attempts"] or 0)))
        return out

    def mark_sent(self, row_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM outbox WHERE id = ?", (int(row_id),))
            self._conn.commit()

    def mark_failed(self, row_id: int, *, attempts: int, error: str, backoff_seconds: int) -> None:
        next_attempt_at = time.time() + max(1, int(backoff_seconds))
        with self._lock:
            self._conn.execute(
                """
                UPDATE outbox
                SET attempts = ?,
                    last_error = ?,
                    next_attempt_at = ?
                WHERE id = ?
                """,
                (int(attempts), str(error or "")[:1000], next_attempt_at, int(row_id)),
            )
            self._conn.commit()

    def size(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(1) AS total FROM outbox").fetchone()
        return int((row["total"] if row else 0) or 0)

    def oldest_pending_seconds(self) -> int:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT created_at
                FROM outbox
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
        if not row or row["created_at"] is None:
            return 0
        age = int(time.time() - float(row["created_at"]))
        return max(0, age)
