from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

import requests

REQUEST_TIMEOUT_SECONDS = 10


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def send_heartbeat(
    *,
    url: str,
    edge_token: str,
    store_id: str,
    agent_id: str,
    version: str,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
) -> Tuple[bool, Optional[int], Optional[str]]:
    payload = {
        "event_name": "edge_heartbeat",
        "source": "edge",
        "data": {
            "store_id": store_id,
            "ts": _utc_timestamp(),
            "agent_id": agent_id,
            "version": version,
        },
    }

    token = (edge_token or "").strip()
    headers = {
        "X-EDGE-TOKEN": token,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout_seconds,
        )
        status = response.status_code
        ok = 200 <= status < 300

        if status >= 400:
            body = (response.text or "").strip()
            if len(body) > 600:
                body = body[:600]
            error = f"HTTP {status}: {body}" if body else f"HTTP {status}"
            return False, status, error

        if ok:
            return True, status, None

        return False, status, f"HTTP {status}"

    except requests.RequestException as exc:
        return False, None, str(exc)
