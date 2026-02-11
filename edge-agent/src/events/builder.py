from typing import Any, Dict, Optional
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_envelope(
    *,
    event_name: str,
    source: str,
    data: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    event_version: int = 1,
    lead_id=None,
    org_id=None
) -> Dict[str, Any]:
    return {
        "event_id": data.get("event_id") or None,
        "event_name": str(event_name),
        "event_version": event_version,
        "ts": data.get("ts") or now_iso(),
        "source": source,
        "lead_id": lead_id,
        "org_id": org_id,
        "data": data,
        "meta": meta or {},
    }
