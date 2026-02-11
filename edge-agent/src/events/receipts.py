import hashlib
import json
from typing import Any, Dict


def compute_receipt_id(payload: Dict[str, Any]) -> str:
    """
    Idempotência: gera um hash estável.
    Use campos relevantes: store_id + camera_id + event_name + bucket/ts
    """
    base = {
        "event_name": payload.get("event_name"),
        "store_id": payload.get("data", {}).get("store_id"),
        "camera_id": payload.get("data", {}).get("camera_id"),
        "ts": payload.get("ts"),
        "event_version": payload.get("event_version", 1),
    }
    raw = json.dumps(base, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
