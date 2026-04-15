from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

import requests

from .cameras import build_auth_headers
from .events import compute_idempotency_key

REQUEST_TIMEOUT_SECONDS = 10
EDGE_EVENTS_ENDPOINT = "/api/edge/events/"
SENSITIVE_KEY_HINTS = (
    "token",
    "password",
    "passwd",
    "secret",
    "authorization",
    "rtsp_url",
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _looks_sensitive_key(key: str) -> bool:
    lowered = str(key or "").strip().lower()
    return any(hint in lowered for hint in SENSITIVE_KEY_HINTS)


def sanitize_event_data(data: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in (data or {}).items():
        if _looks_sensitive_key(str(key)):
            continue
        if isinstance(value, dict):
            sanitized[key] = sanitize_event_data(value)
            continue
        if isinstance(value, list):
            out: list[Any] = []
            for item in value:
                if isinstance(item, dict):
                    out.append(sanitize_event_data(item))
                else:
                    out.append(item)
            sanitized[key] = out
            continue
        sanitized[key] = value
    return sanitized


def send_onboarding_event(
    *,
    cloud_base_url: str,
    edge_token: str,
    event_name: str,
    data: dict[str, Any],
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
) -> Tuple[bool, Optional[int], Optional[str]]:
    safe_data = sanitize_event_data(data or {})
    if "ts" not in safe_data:
        safe_data["ts"] = _utc_timestamp()

    envelope = {
        "event_name": str(event_name or "").strip(),
        "source": "edge",
        "data": safe_data,
    }
    receipt_id = compute_idempotency_key(
        event_name=envelope["event_name"],
        data=safe_data,
        ts=str(safe_data.get("ts") or ""),
        bucket_minutes=1,
    )
    envelope["receipt_id"] = receipt_id
    envelope["idempotency_key"] = receipt_id

    url = f"{str(cloud_base_url or '').rstrip('/')}{EDGE_EVENTS_ENDPOINT}"
    headers = build_auth_headers(edge_token)
    try:
        response = requests.post(url, json=envelope, headers=headers, timeout=timeout_seconds)
        if 200 <= response.status_code < 300:
            return True, response.status_code, None
        detail = None
        try:
            payload = response.json()
            detail = payload.get("detail") or payload.get("error") or payload
        except Exception:
            detail = response.text.strip()[:500] if response.text else None
        return False, response.status_code, f"HTTP {response.status_code}: {detail}"
    except requests.RequestException as exc:
        return False, None, str(exc)
