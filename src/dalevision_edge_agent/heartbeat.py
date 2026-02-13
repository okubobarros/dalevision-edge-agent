from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

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
    extra_data: Optional[dict[str, Any]] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    data = {
        "store_id": store_id,
        "ts": _utc_timestamp(),
        "agent_id": agent_id,
        "version": version,
    }
    if extra_data:
        data.update(extra_data)

    payload = {
        "event_name": "edge_heartbeat",
        "source": "edge",
        "data": data,
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

        # tenta extrair erro do backend, senão cai no texto bruto
        detail = None
        try:
            j = response.json()
            detail = j.get("detail") or j.get("error") or j
        except Exception:
            detail = response.text.strip()[:500] if response.text else None

        return False, status, f"HTTP {status}: {detail}"
    except requests.RequestException as exc:
        return False, None, str(exc)
