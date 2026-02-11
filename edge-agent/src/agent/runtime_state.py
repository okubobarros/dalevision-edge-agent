from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
from typing import Optional, Dict, Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentRuntimeState:
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    agent_running: bool = False
    heartbeat_only: bool = False
    last_heartbeat_sent_at: Optional[str] = None
    last_heartbeat_ok: Optional[bool] = None
    last_heartbeat_http_status: Optional[int] = None
    last_heartbeat_error: Optional[str] = None
    last_backend_seen_ok_at: Optional[str] = None
    sent_ok: int = 0
    sent_fail: int = 0

    def set_running(self, running: bool, heartbeat_only: Optional[bool] = None) -> None:
        with self._lock:
            self.agent_running = running
            if heartbeat_only is not None:
                self.heartbeat_only = bool(heartbeat_only)

    def record_flush(
        self,
        ok: bool,
        status: Optional[int],
        error: Optional[str],
        sent_ok: int,
        sent_fail: int,
        backend_ok: bool,
    ) -> None:
        now = _now_iso()
        with self._lock:
            self.last_heartbeat_sent_at = now
            self.last_heartbeat_ok = bool(ok)
            self.last_heartbeat_http_status = status
            self.last_heartbeat_error = error
            self.sent_ok += int(sent_ok)
            self.sent_fail += int(sent_fail)
            if backend_ok:
                self.last_backend_seen_ok_at = now

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "agent_running": self.agent_running,
                "heartbeat_only": self.heartbeat_only,
                "last_heartbeat_sent_at": self.last_heartbeat_sent_at,
                "last_heartbeat_ok": self.last_heartbeat_ok,
                "last_heartbeat_http_status": self.last_heartbeat_http_status,
                "last_heartbeat_error": self.last_heartbeat_error,
                "last_backend_seen_ok_at": self.last_backend_seen_ok_at,
                "sent_ok": self.sent_ok,
                "sent_fail": self.sent_fail,
            }


RUNTIME_STATE = AgentRuntimeState()
