from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import socket
import time
from typing import Any, Optional
from urllib.parse import urlparse

import requests

CAMERA_LIST_ENDPOINTS = (
    "/api/edge/cameras/",
    "/api/v1/stores/{store_id}/cameras",
)
ROI_ENDPOINTS = (
    "/api/edge/cameras/{camera_id}/roi/latest",
    "/api/v1/cameras/{camera_id}/roi/latest",
)
EVENTS_ENDPOINT = "/api/edge/events/"

HTTP_TIMEOUT_SECONDS = 5
HEALTHCHECK_TIMEOUT_SECONDS = 3
HTTP_RETRY_DELAYS_SECONDS = (0.5, 1.0, 2.0)
CAMERA_SYNC_INTERVAL_SECONDS = 60


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_base_url(base_url: str) -> str:
    return (base_url or "").rstrip("/")


def _headers(edge_token: str) -> dict[str, str]:
    return {"X-EDGE-TOKEN": edge_token}


def _extract_camera_id(camera: dict[str, Any]) -> str:
    return str(
        camera.get("camera_id")
        or camera.get("id")
        or camera.get("uuid")
        or ""
    ).strip()


def _extract_rtsp_url(camera: dict[str, Any]) -> str:
    for key in ("rtsp_url", "stream_url", "rtsp", "url"):
        value = camera.get(key)
        if value:
            return str(value).strip()
    return ""


def _request_json_with_backoff(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    timeout_seconds: int,
    logger: logging.Logger,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None,
) -> tuple[Optional[dict[str, Any]], Optional[int], Optional[str]]:
    last_error: Optional[str] = None
    for attempt in range(len(HTTP_RETRY_DELAYS_SECONDS) + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout_seconds,
            )
            status = response.status_code
            if 200 <= status < 300:
                try:
                    return response.json(), status, None
                except Exception:
                    return {}, status, None
            text = response.text.strip()[:500] if response.text else ""
            return None, status, text or f"HTTP {status}"
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt >= len(HTTP_RETRY_DELAYS_SECONDS):
                break
            delay = HTTP_RETRY_DELAYS_SECONDS[attempt]
            logger.warning(
                "HTTP retry %s for %s in %.1fs (%s)",
                attempt + 1,
                url,
                delay,
                last_error,
            )
            time.sleep(delay)
    return None, None, last_error


def fetch_cameras(
    *,
    cloud_base_url: str,
    edge_token: str,
    store_id: str,
    timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    logger: Optional[logging.Logger] = None,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    base_url = _normalize_base_url(cloud_base_url)
    headers = _headers(edge_token)

    for endpoint in CAMERA_LIST_ENDPOINTS:
        path = endpoint.format(store_id=store_id)
        url = f"{base_url}{path}"
        params = {"store_id": store_id} if "edge/cameras" in endpoint else None
        payload, status, error = _request_json_with_backoff(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            timeout_seconds=timeout_seconds,
            logger=logger,
        )
        if payload is None:
            logger.warning(
                "Camera list fetch failed on %s (status=%s error=%s)",
                url,
                status,
                error,
            )
            continue

        cameras = payload.get("results") or payload.get("data") or payload
        if isinstance(cameras, list):
            return cameras, None
        return [], None

    return [], "Camera list endpoint unavailable"


def _cache_root(cache_dir: Optional[Path]) -> Path:
    base = cache_dir or (Path.cwd() / "cache" / "roi")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _cache_file(camera_id: str, cache_dir: Optional[Path]) -> Path:
    return _cache_root(cache_dir) / f"{camera_id}.json"


def _load_cached_roi(
    *,
    camera_id: str,
    cache_dir: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    path = _cache_file(camera_id, cache_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cached_roi(
    *,
    camera_id: str,
    payload: dict[str, Any],
    cache_dir: Optional[Path] = None,
) -> None:
    path = _cache_file(camera_id, cache_dir)
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def _extract_roi_version(payload: dict[str, Any]) -> str:
    direct = payload.get("version")
    if direct:
        return str(direct)
    data = payload.get("data")
    if isinstance(data, dict) and data.get("version"):
        return str(data["version"])
    return "unknown"


def fetch_roi(
    camera_id: str,
    *,
    cloud_base_url: str,
    edge_token: str,
    expected_version: Optional[str] = None,
    timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    cache_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> tuple[Optional[dict[str, Any]], Optional[str], bool, Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    cached = _load_cached_roi(camera_id=camera_id, cache_dir=cache_dir)
    cached_version = (
        str(cached.get("version")) if isinstance(cached, dict) and cached.get("version") else None
    )
    if expected_version and cached_version == expected_version:
        logger.info(
            "camera_id=%s ROI cache hit for version=%s (skip download)",
            camera_id,
            expected_version,
        )
        return cached, cached_version, True, None

    base_url = _normalize_base_url(cloud_base_url)
    headers = _headers(edge_token)
    for endpoint in ROI_ENDPOINTS:
        url = f"{base_url}{endpoint.format(camera_id=camera_id)}"
        payload, status, error = _request_json_with_backoff(
            method="GET",
            url=url,
            headers=headers,
            timeout_seconds=timeout_seconds,
            logger=logger,
        )
        if payload is None:
            logger.warning(
                "camera_id=%s ROI fetch failed on %s (status=%s error=%s)",
                camera_id,
                url,
                status,
                error,
            )
            continue

        version = _extract_roi_version(payload)
        to_cache = dict(payload)
        to_cache["version"] = version
        _save_cached_roi(camera_id=camera_id, payload=to_cache, cache_dir=cache_dir)
        return to_cache, version, False, None

    return cached, cached_version, True, "ROI endpoint unavailable"


def check_camera_health(
    camera: dict[str, Any],
    *,
    timeout_seconds: int = HEALTHCHECK_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    camera_id = _extract_camera_id(camera)
    rtsp_url = _extract_rtsp_url(camera)
    checked_at = _utc_timestamp()

    if not rtsp_url:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": "rtsp_url_missing",
            "connect_ms": None,
            "checked_at": checked_at,
        }

    parsed = urlparse(rtsp_url)
    host = parsed.hostname
    port = parsed.port or 554
    if not host:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": "rtsp_host_missing",
            "connect_ms": None,
            "checked_at": checked_at,
        }

    started = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout_seconds)
        try:
            sock.settimeout(timeout_seconds)
            connect_ms = int((time.perf_counter() - started) * 1000)
        finally:
            sock.close()
    except socket.timeout:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": "timeout",
            "connect_ms": None,
            "checked_at": checked_at,
        }
    except OSError as exc:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": str(exc),
            "connect_ms": None,
            "checked_at": checked_at,
        }

    status = "online" if connect_ms <= 1500 else "degraded"
    return {
        "camera_id": camera_id,
        "status": status,
        "error": None if status == "online" else "slow_connect",
        "connect_ms": connect_ms,
        "checked_at": checked_at,
    }


def send_camera_health_event(
    *,
    cloud_base_url: str,
    edge_token: str,
    store_id: str,
    agent_id: str,
    camera_health: dict[str, Any],
    timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    logger: Optional[logging.Logger] = None,
) -> tuple[bool, Optional[int], Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    url = f"{_normalize_base_url(cloud_base_url)}{EVENTS_ENDPOINT}"
    payload = {
        "event_name": "camera.health",
        "source": "edge",
        "data": {
            "store_id": store_id,
            "agent_id": agent_id,
            "camera_id": camera_health.get("camera_id"),
            "status": camera_health.get("status"),
            "error": camera_health.get("error"),
            "connect_ms": camera_health.get("connect_ms"),
            "checked_at": camera_health.get("checked_at"),
        },
    }
    try:
        response = requests.post(
            url,
            headers=_headers(edge_token),
            json=payload,
            timeout=timeout_seconds,
        )
        status = response.status_code
        ok = 200 <= status < 300
        if ok:
            return True, status, None
        detail = response.text.strip()[:500] if response.text else f"HTTP {status}"
        logger.warning(
            "camera_id=%s health event rejected (status=%s detail=%s)",
            camera_health.get("camera_id"),
            status,
            detail,
        )
        return False, status, detail
    except requests.RequestException as exc:
        return False, None, str(exc)


def build_camera_heartbeat_fields(
    states: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    summary: list[dict[str, Any]] = []
    counts = {"online": 0, "degraded": 0, "offline": 0}
    for camera_id in sorted(states.keys()):
        state = states[camera_id]
        status = str(state.get("status") or "offline")
        if status not in counts:
            status = "offline"
        counts[status] += 1
        summary.append(
            {
                "camera_id": camera_id,
                "status": status,
                "roi_version": state.get("roi_version"),
            }
        )

    return {
        "cameras_total": len(summary),
        "cameras_online": counts["online"],
        "cameras_degraded": counts["degraded"],
        "cameras_offline": counts["offline"],
        "cameras": summary,
    }
