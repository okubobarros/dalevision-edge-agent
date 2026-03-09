from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import shutil
import time
from typing import Any, Optional
from urllib.parse import urlparse

import requests

CAMERA_LIST_ENDPOINTS = (
    "/api/v1/stores/{store_id}/cameras/",
)
ROI_ENDPOINTS = (
    "/api/v1/cameras/{camera_id}/roi/latest",
)
HEALTH_ENDPOINT = "/api/v1/cameras/{camera_id}/health/"
EDGE_EVENTS_ENDPOINT = "/api/edge/events/"

HTTP_TIMEOUT_SECONDS = 5
HEALTHCHECK_TIMEOUT_SECONDS = 3
HTTP_RETRY_DELAYS_SECONDS = (0.5, 1.0, 2.0)
CAMERA_SYNC_INTERVAL_SECONDS = 30
AUTH_FAILURE_STATUSES = {401, 403}
MAX_AUTH_FAILURES = 5


class AuthFailureTracker:
    def __init__(self, max_failures: int = MAX_AUTH_FAILURES) -> None:
        self.max_failures = max_failures
        self.consecutive = 0

    def register(self, status: Optional[int]) -> bool:
        if status in AUTH_FAILURE_STATUSES:
            self.consecutive += 1
            return self.consecutive >= self.max_failures
        if status is not None:
            self.consecutive = 0
        return False

    def reset(self) -> None:
        self.consecutive = 0


def _resolve_timeout_seconds(default: int, env_name: str) -> int:
    raw = (os.getenv(env_name) or os.getenv("EDGE_HTTP_TIMEOUT_SECONDS") or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_base_url(base_url: str) -> str:
    return (base_url or "").rstrip("/")


def build_auth_headers(edge_token: str) -> dict[str, str]:
    token = edge_token or ""
    return {
        "Authorization": f"Bearer {token}",
        "X-EDGE-TOKEN": token,
    }


def _format_auth_header_debug(headers: dict[str, str]) -> str:
    token = headers.get("X-EDGE-TOKEN") or ""
    prefix = token[:6] if token else ""
    length = len(token)
    return f"X-EDGE-TOKEN prefix={prefix} len={length}"


def _extract_camera_id(camera: dict[str, Any]) -> str:
    return str(
        camera.get("camera_id")
        or camera.get("id")
        or camera.get("uuid")
        or ""
    ).strip()


def _extract_rtsp_url(camera: dict[str, Any]) -> str:
    for key in ("rtsp_url", "rtsp_url_masked", "stream_url", "rtsp", "url"):
        value = camera.get(key)
        if value:
            return str(value).strip()
    return ""


def mask_rtsp_url(rtsp_url: str) -> str:
    if not rtsp_url:
        return ""
    parsed = urlparse(rtsp_url)
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        safe_user = parsed.username or "user"
        netloc = f"{safe_user}:***@{netloc}"
        return parsed._replace(netloc=netloc).geturl()
    return rtsp_url


def _extract_rtsp_credentials(camera: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    username = camera.get("username") or camera.get("user") or camera.get("rtsp_user")
    password = camera.get("password") or camera.get("pass") or camera.get("rtsp_pass")
    user = str(username).strip() if username else None
    pwd = str(password).strip() if password else None
    return (user or None), (pwd or None)


def _extract_rtsp_host_port(camera: dict[str, Any]) -> tuple[Optional[str], int]:
    host = None
    for key in ("rtsp_host", "host", "ip", "camera_ip"):
        value = camera.get(key)
        if value:
            host = str(value).strip()
            break
    port_raw = camera.get("rtsp_port") or camera.get("port")
    if isinstance(port_raw, int):
        port = port_raw
    else:
        try:
            port = int(str(port_raw))
        except Exception:
            port = 554
    return host, port


def _request_json_with_backoff(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    timeout_seconds: int,
    logger: logging.Logger,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None,
    auth_tracker: Optional[AuthFailureTracker] = None,
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
                if auth_tracker:
                    auth_tracker.reset()
                try:
                    return response.json(), status, None
                except Exception:
                    return {}, status, None
            text = response.text.strip()[:500] if response.text else ""
            if auth_tracker and auth_tracker.register(status):
                return None, status, text or "auth_failure_threshold"
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
    auth_tracker: Optional[AuthFailureTracker] = None,
) -> tuple[list[dict[str, Any]], Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    timeout_seconds = _resolve_timeout_seconds(timeout_seconds, "EDGE_CAMERA_LIST_TIMEOUT_SECONDS")
    base_url = _normalize_base_url(cloud_base_url)
    headers = build_auth_headers(edge_token)
    auth_debug = _format_auth_header_debug(headers)

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
            auth_tracker=auth_tracker,
        )
        if payload is None:
            logger.warning(
                "Camera list fetch failed url=%s status=%s error=%s auth=%s",
                url,
                status,
                error,
                auth_debug,
            )
            if status in AUTH_FAILURE_STATUSES:
                logger.warning(
                    "Camera list auth failed url=%s status=%s hint=token invalido ou sem permissao",
                    url,
                    status,
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
    auth_tracker: Optional[AuthFailureTracker] = None,
) -> tuple[Optional[dict[str, Any]], Optional[str], bool, Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    timeout_seconds = _resolve_timeout_seconds(timeout_seconds, "EDGE_ROI_TIMEOUT_SECONDS")
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
    headers = build_auth_headers(edge_token)
    for endpoint in ROI_ENDPOINTS:
        url = f"{base_url}{endpoint.format(camera_id=camera_id)}"
        payload, status, error = _request_json_with_backoff(
            method="GET",
            url=url,
            headers=headers,
            timeout_seconds=timeout_seconds,
            logger=logger,
            auth_tracker=auth_tracker,
        )
        if payload is None:
            logger.warning(
                "camera_id=%s ROI fetch failed on %s (status=%s error=%s)",
                camera_id,
                url,
                status,
                error,
            )
            if status in AUTH_FAILURE_STATUSES:
                logger.warning(
                    "ROI auth failed url=%s status=%s hint=token invalido ou sem permissao",
                    url,
                    status,
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
    perform_describe: bool = False,
    rtsp_url_override: Optional[str] = None,
) -> dict[str, Any]:
    camera_id = _extract_camera_id(camera)
    rtsp_url = rtsp_url_override or _extract_rtsp_url(camera)
    checked_at = _utc_timestamp()

    host = None
    port = 554
    if rtsp_url:
        parsed = urlparse(rtsp_url)
        host = parsed.hostname
        port = parsed.port or 554
    if not host:
        host, port = _extract_rtsp_host_port(camera)

    if not host:
        return {
            "camera_id": camera_id,
            "status": "error",
            "error": "rtsp_host_missing" if rtsp_url else "rtsp_url_missing",
            "latency_ms": None,
            "checked_at": checked_at,
        }

    started = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout_seconds)
        try:
            sock.settimeout(timeout_seconds)
            latency_ms = int((time.perf_counter() - started) * 1000)
            if perform_describe:
                describe_url = rtsp_url or f"rtsp://{host}:{port}/"
                request = (
                    f"DESCRIBE {describe_url} RTSP/1.0\r\n"
                    "CSeq: 1\r\n"
                    "User-Agent: dalevision-edge-agent\r\n"
                    "Accept: application/sdp\r\n\r\n"
                ).encode("ascii", errors="ignore")
                try:
                    sock.sendall(request)
                    response = sock.recv(4096)
                except OSError as exc:
                    return {
                        "camera_id": camera_id,
                        "status": "degraded",
                        "error": f"describe_failed:{exc}",
                        "latency_ms": latency_ms,
                        "checked_at": checked_at,
                    }
                if response.startswith(b"RTSP/1.0"):
                    first_line = response.split(b"\r\n", 1)[0].decode("ascii", errors="ignore")
                    if " 401 " in first_line or " 403 " in first_line:
                        return {
                            "camera_id": camera_id,
                            "status": "error",
                            "error": "unauthorized",
                            "latency_ms": latency_ms,
                            "checked_at": checked_at,
                        }
                else:
                    return {
                        "camera_id": camera_id,
                        "status": "degraded",
                        "error": "describe_invalid_response",
                        "latency_ms": latency_ms,
                        "checked_at": checked_at,
                    }
        finally:
            sock.close()
    except socket.timeout:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": "timeout",
            "latency_ms": None,
            "checked_at": checked_at,
        }
    except OSError as exc:
        return {
            "camera_id": camera_id,
            "status": "offline",
            "error": str(exc),
            "latency_ms": None,
            "checked_at": checked_at,
        }

    status = "online" if latency_ms <= 1500 else "degraded"
    return {
        "camera_id": camera_id,
        "status": status,
        "error": None if status == "online" else "slow_connect",
        "latency_ms": latency_ms,
        "checked_at": checked_at,
    }


def send_camera_health_event(
    *,
    cloud_base_url: str,
    edge_token: str,
    store_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    camera_health: dict[str, Any],
    timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    logger: Optional[logging.Logger] = None,
    auth_tracker: Optional[AuthFailureTracker] = None,
) -> tuple[bool, Optional[int], Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    camera_id = camera_health.get("camera_id")
    url = f"{_normalize_base_url(cloud_base_url)}{EDGE_EVENTS_ENDPOINT}"
    event_payload = {
        "store_id": store_id or camera_health.get("store_id") or "",
        "agent_id": agent_id or camera_health.get("agent_id") or "",
        "event_name": "camera_health",
        "ts": camera_health.get("checked_at") or _utc_timestamp(),
        "camera_id": camera_id,
        "status": camera_health.get("status"),
        "latency_ms": camera_health.get("latency_ms"),
        "error": camera_health.get("error"),
    }
    snapshot_url = camera_health.get("snapshot_url")
    if snapshot_url:
        event_payload["snapshot_url"] = snapshot_url
    if "snapshot_taken" in camera_health:
        event_payload["snapshot_taken"] = camera_health.get("snapshot_taken")
    if "snapshot_local_path" in camera_health:
        event_payload["snapshot_local_path"] = camera_health.get("snapshot_local_path")
    if "snapshot_status" in camera_health:
        event_payload["snapshot_status"] = camera_health.get("snapshot_status")
    envelope = {
        "event_name": "camera_health",
        "source": "edge",
        "ts": event_payload["ts"],
        "data": event_payload,
    }
    response, status, error = _request_json_with_backoff(
        method="POST",
        url=url,
        headers=build_auth_headers(edge_token),
        json_body=envelope,
        timeout_seconds=timeout_seconds,
        logger=logger,
        auth_tracker=auth_tracker,
    )
    ok = response is not None and status is not None and 200 <= status < 300
    if ok:
        logger.info(
            "camera_id=%s health POST %s status=%s",
            camera_id,
            url,
            status,
        )
        return True, status, None
    detail = error or (f"HTTP {status}" if status else None)
    logger.warning(
        "camera_id=%s health POST rejected url=%s status=%s detail=%s",
        camera_health.get("camera_id"),
        url,
        status,
        detail,
    )
    if status in AUTH_FAILURE_STATUSES:
        logger.warning(
            "[CAMERA_HEALTH] auth_fail url=%s status=%s hint=token invalido ou sem permissao",
            url,
            status,
        )
    return False, status, detail


def send_vision_metrics_event(
    *,
    cloud_base_url: str,
    edge_token: str,
    payload: dict[str, Any],
    timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    logger: Optional[logging.Logger] = None,
) -> tuple[bool, Optional[int], Optional[str]]:
    logger = logger or logging.getLogger("dalevision-edge-agent")
    url = f"{_normalize_base_url(cloud_base_url)}{EDGE_EVENTS_ENDPOINT}"
    envelope = {
        "event_name": "vision.metrics.v1",
        "source": "edge",
        "ts": payload.get("ts"),
        "data": payload,
    }
    response, status, error = _request_json_with_backoff(
        method="POST",
        url=url,
        headers=build_auth_headers(edge_token),
        json_body=envelope,
        timeout_seconds=timeout_seconds,
        logger=logger,
    )
    ok = response is not None and status is not None and 200 <= status < 300
    if ok:
        logger.info("vision metrics POST %s status=%s", url, status)
        return True, status, None
    detail = error or (f"HTTP {status}" if status else None)
    logger.warning("vision metrics POST rejected url=%s status=%s detail=%s", url, status, detail)
    return False, status, detail


def build_rtsp_candidates(camera: dict[str, Any]) -> list[str]:
    rtsp_url = _extract_rtsp_url(camera)
    host, port = _extract_rtsp_host_port(camera)
    user, pwd = _extract_rtsp_credentials(camera)
    if not host:
        return [rtsp_url] if rtsp_url else []

    auth = ""
    if user and pwd:
        auth = f"{user}:{pwd}@"
    base = f"rtsp://{auth}{host}:{port}"

    channel = camera.get("channel") or camera.get("rtsp_channel") or 1
    try:
        channel_int = int(channel)
    except Exception:
        channel_int = 1

    connection_type = str(camera.get("connection_type") or "").lower()
    is_nvr = connection_type in {"nvr", "dvr"} or camera.get("channel") is not None

    presets: list[str] = []
    if is_nvr:
        presets.extend(
            [
                f"{base}/Streaming/Channels/{channel_int}01",
                f"{base}/Channels/{channel_int}01",
                f"{base}/cam/realmonitor?channel={channel_int}&subtype=0",
            ]
        )
    else:
        presets.extend(
            [
                f"{base}/stream1",
                f"{base}/Streaming/Channels/101",
                f"{base}/h264/ch1/main/av_stream",
            ]
        )

    candidates: list[str] = []
    if rtsp_url:
        candidates.append(rtsp_url)
    for preset in presets:
        if preset not in candidates:
            candidates.append(preset)
    return candidates


def _try_import_cv2():
    try:
        import cv2  # type: ignore

        return cv2
    except Exception:
        return None


def _ffmpeg_path() -> Optional[str]:
    path = shutil.which("ffmpeg")
    if path:
        return path
    candidates = [
        Path.cwd() / "ffmpeg.exe",
        Path.cwd() / "bin" / "ffmpeg.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def detect_snapshot_support(logger: logging.Logger) -> dict[str, Optional[str]]:
    cv2 = _try_import_cv2()
    if cv2 is not None:
        version = getattr(cv2, "__version__", "unknown")
        logger.info("SNAPCV OpenCV disponível: sim (versao=%s)", version)
        return {"opencv": "yes", "ffmpeg": _ffmpeg_path(), "opencv_version": str(version)}

    logger.info("SNAPCV OpenCV disponível: nao")
    ffmpeg = _ffmpeg_path()
    if ffmpeg:
        logger.info("SNAPFF ffmpeg disponível: sim (%s)", ffmpeg)
        return {"opencv": "no", "ffmpeg": ffmpeg, "opencv_version": None}

    logger.warning(
        "SNAPNO Snapshot indisponivel. Instale ffmpeg e adicione ao PATH "
        "ou use um pacote com OpenCV."
    )
    return {"opencv": "no", "ffmpeg": None, "opencv_version": None}


def capture_snapshot_if_possible(
    *,
    camera_id: str,
    rtsp_url: str,
    logger: logging.Logger,
    timeout_seconds: int = 5,
) -> dict[str, Optional[str]]:
    cv2 = _try_import_cv2()
    if cv2 is None:
        logger.info("[EDGE] OpenCV não disponível; tentando fallback ffmpeg")
        ffmpeg = _ffmpeg_path()
        if not ffmpeg:
            logger.info("SNAPNO camera_id=%s snapshot skipped (ffmpeg not available)", camera_id)
            return {"snapshot_status": "skip", "snapshot_local_path": None}
        result = _capture_snapshot_ffmpeg(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            logger=logger,
            timeout_seconds=timeout_seconds,
            ffmpeg_path=ffmpeg,
        )
        if result is None:
            return {"snapshot_status": "error", "snapshot_local_path": None}
        return {"snapshot_status": "ok", "snapshot_local_path": result}

    snapshots_dir = Path.cwd() / "cache" / "snapshots"
    output_dir = snapshots_dir / camera_id
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}.jpg"
    output_path = output_dir / filename

    cap = cv2.VideoCapture(rtsp_url)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_seconds * 1000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_seconds * 1000)
    except Exception:
        pass

    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            logger.info("SNAPERR camera_id=%s snapshot capture failed", camera_id)
            return {"snapshot_status": "error", "snapshot_local_path": None}
        cv2.imwrite(str(output_path), frame)
        logger.info("camera_id=%s snapshot captured path=%s", camera_id, output_path)
        return {"snapshot_status": "ok", "snapshot_local_path": str(output_path)}
    finally:
        cap.release()


def _capture_snapshot_ffmpeg(
    *,
    camera_id: str,
    rtsp_url: str,
    logger: logging.Logger,
    timeout_seconds: int,
    ffmpeg_path: str,
) -> Optional[str]:
    snapshots_dir = Path.cwd() / "cache" / "snapshots"
    output_dir = snapshots_dir / camera_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{int(time.time())}.jpg"
    command = [
        ffmpeg_path,
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-y",
        str(output_path),
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            text=True,
        )
    except subprocess.TimeoutExpired:
        logger.info("SNAPTO camera_id=%s snapshot ffmpeg timeout", camera_id)
        return None
    except OSError as exc:
        logger.info("SNAPERR camera_id=%s snapshot ffmpeg error=%s", camera_id, exc)
        return None

    if result.returncode != 0 or not output_path.exists():
        stderr = (result.stderr or "").strip().splitlines()
        detail = stderr[-1] if stderr else "ffmpeg_failed"
        logger.info("SNAPERR camera_id=%s snapshot ffmpeg failed: %s", camera_id, detail)
        return None

    logger.info("camera_id=%s snapshot captured path=%s", camera_id, output_path)
    return str(output_path)


def build_camera_heartbeat_fields(
    states: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    summary: list[dict[str, Any]] = []
    counts = {"online": 0, "degraded": 0, "offline": 0, "unknown": 0}
    for camera_id in sorted(states.keys()):
        state = states[camera_id]
        status = str(state.get("status") or "unknown")
        if status not in counts:
            status = "unknown"
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
        "cameras_unknown": counts["unknown"],
        "cameras": summary,
    }
