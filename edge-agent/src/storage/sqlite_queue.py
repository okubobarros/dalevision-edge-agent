import os
import sqlite3
import json
import time
import threading
from typing import Any, Dict, List, Tuple


class SqliteQueue:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

        # garante que o diretório existe (Windows)
        db_dir = os.path.dirname(os.path.abspath(self.path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """
        Cria a tabela de outbox (offline-first).
        """
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT UNIQUE,
                    payload_json TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at REAL NOT NULL,
                    next_attempt_at REAL DEFAULT 0
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_outbox_next_attempt ON outbox(next_attempt_at)"
            )
            self._conn.commit()

    def enqueue(self, payload: Dict[str, Any]) -> bool:
        """
        Insere evento no outbox.
        receipt_id deve vir dentro do payload.
        """
        try:
            receipt_id = payload["receipt_id"]
            with self._lock:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO outbox
                    (receipt_id, payload_json, created_at, next_attempt_at)
                    VALUES (?, ?, ?, 0)
                    """,
                    (
                        receipt_id,
                        json.dumps(payload, ensure_ascii=False),
                        time.time(),
                    ),
                )
                self._conn.commit()
            return True
        except Exception as e:
            print("❌ enqueue error:", e)
            return False

    def peek_batch(self, limit: int = 50) -> List[Tuple[int, str, Dict[str, Any], int]]:
        """
        Retorna eventos prontos para envio.
        """
        now = time.time()
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, receipt_id, payload_json, attempts
                FROM outbox
                WHERE next_attempt_at <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (now, limit),
            ).fetchall()

        out = []
        for row in rows:
            out.append(
                (
                    row["id"],
                    row["receipt_id"],
                    json.loads(row["payload_json"]),
                    row["attempts"],
                )
            )
        return out

    def mark_sent(self, row_id: int):
        with self._lock:
            self._conn.execute("DELETE FROM outbox WHERE id = ?", (row_id,))
            self._conn.commit()

    def mark_failed(self, row_id: int, error: str, attempts: int, backoff_seconds: int):
        next_at = time.time() + backoff_seconds
        with self._lock:
            self._conn.execute(
                """
                UPDATE outbox
                SET last_error = ?, attempts = ?, next_attempt_at = ?
                WHERE id = ?
                """,
                (error[:1000], attempts, next_at, row_id),
            )
            self._conn.commit()
