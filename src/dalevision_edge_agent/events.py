from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _parse_iso_ts(raw_ts: str | None) -> datetime:
    if not raw_ts:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def compute_idempotency_key(
    *,
    event_name: str,
    data: dict[str, Any] | None,
    ts: str | None,
    bucket_seconds: int = 5,
    bucket_minutes: int | None = None,
) -> str:
    payload = data or {}
    dt = _parse_iso_ts(ts)

    # Backward compatibility: older callers pass bucket_minutes.
    # If provided, it takes precedence and aligns bucket to minute windows.
    if bucket_minutes is not None:
        minutes = max(1, int(bucket_minutes))
        bucket_start_minute = (dt.minute // minutes) * minutes
        dt = dt.replace(minute=bucket_start_minute, second=0, microsecond=0)
        ts_bucket = dt.isoformat()
    else:
        # Default 5-second bucketing.
        seconds = dt.second + (dt.microsecond / 1_000_000.0)
        safe_bucket_seconds = max(1, int(bucket_seconds))
        bucketed_second = int(seconds // safe_bucket_seconds) * safe_bucket_seconds
        ts_bucket = dt.replace(second=bucketed_second, microsecond=0).isoformat()
    
    base = {
        "event_name": event_name,
        "store_id": payload.get("store_id"),
        "camera_id": payload.get("camera_id"),
        "event_type": payload.get("event_type"),
        "roi_entity_id": payload.get("roi_entity_id"),
        "metric_type": payload.get("metric_type"),
        "track_id": payload.get("track_id") or payload.get("global_id"),
        "ts_bucket": ts_bucket,
    }
    raw = json.dumps(base, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
