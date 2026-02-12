from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

import requests

REQUEST_TIMEOUT_SECONDS = 10


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _format_error(status: int, response_text: str) -> str:
    # tenta extrair {"detail": "..."} quando existir
    try:
        data = requests.models.complexjson.loads(response_text)  # type: ignore[attr-defined]
        if isinstance(data, dict) and "detail" in data:
            return f"HTTP {status}: {data['detail']}"
    except Exception:
        pass

    snippet = (response_text or "").strip().replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    return f"HTTP {status}: {snippet or 'Erro sem corpo'}"


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
        error = None if ok else _format_error(status, response.text)
        return ok, status, error
    except requests.RequestException as exc:
        return False, None, str(exc)
