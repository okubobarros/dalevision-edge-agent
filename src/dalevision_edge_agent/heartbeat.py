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
    headers = {"X-EDGE-TOKEN": edge_token}

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout_seconds,
        )
        status = response.status_code
        ok = 200 <= status < 300

        if ok:
            return True, status, None

        # tenta extrair body (muito útil p/ 403 Edge token inválido etc.)
        body = None
        try:
            body = response.text
        except Exception:
            body = None

        msg = f"HTTP {status}"
        if body:
            msg = f"{msg}: {body}"

        return False, status, msg

    except requests.RequestException as exc:
        return False, None, str(exc)
