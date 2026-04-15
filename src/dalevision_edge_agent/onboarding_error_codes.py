from __future__ import annotations

from typing import Optional


def map_camera_health_error_to_code(camera_error: str) -> str:
    value = str(camera_error or "").strip().lower()
    if value in {"auth_failed", "unauthorized", "401", "403"}:
        return "NVR_AUTH_FAIL"
    if value in {"rtsp_timeout", "timeout", "timed_out"}:
        return "RTSP_TIMEOUT"
    return "NVR_UNREACHABLE"


def map_heartbeat_failure_to_code(status_code: Optional[int]) -> str:
    if status_code in {401, 403}:
        return "HEARTBEAT_REJECTED"
    return "NVR_UNREACHABLE"
