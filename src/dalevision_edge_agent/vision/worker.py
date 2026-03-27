from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import dotenv_values

from ..cameras import _ffmpeg_path, build_auth_headers, fetch_roi, mask_rtsp_url
from ..events import compute_idempotency_key
from .outbox import VisionOutbox
from .geometry import line_side, point_in_polygon
from .roi_yaml import load_roi_yaml
from .sources.video import VideoFrameSource


def _now_ts() -> float:
    return time.time()


def _bucket_start(ts: float, bucket_seconds: int) -> int:
    return int(ts // bucket_seconds) * bucket_seconds


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _redact_rtsp_secrets(text: str, rtsp_url: str) -> str:
    if not text:
        return ""
    safe_url = mask_rtsp_url(rtsp_url)
    redacted = text.replace(rtsp_url, safe_url)
    redacted = re.sub(r"(rtsp://[^\\s/@]+:)[^@\\s]+@", r"\\1***@", redacted)
    return redacted


def _safe_json_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _env_str(name: str, default: str) -> str:
    import os
    return os.getenv(name, default)


def _slug(text: str) -> str:
    value = (text or "").strip().lower()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


EDGE_CAMERA_ENDPOINTS = (
    "/api/edge/cameras/",
    "/api/edge/stores/{store_id}/cameras/",
)


@dataclass
class VisionConfig:
    enabled: bool = False
    source: str = "rtsp"
    bucket_seconds: int = 30
    poll_seconds: int = 5
    max_cameras: int = 10
    snapshot_timeout_seconds: int = 10
    role_map: Dict[str, str] = field(default_factory=dict)
    alerts_enabled: bool = False
    inactivity_seconds: int = 120
    inactivity_cooldown_seconds: int = 300
    queue_size_threshold: int = 3
    queue_wait_seconds: int = 60
    queue_cooldown_seconds: int = 180
    phone_enabled: bool = False
    phone_seconds: int = 30
    phone_cooldown_seconds: int = 300
    phone_class_id: int = 67
    blur_enabled: bool = True
    blur_strength: int = 41
    embed_thumbnail: bool = False
    thumbnail_width: int = 320
    frame_stride: int = 1
    video_path: str = ""
    video_realtime: bool = False
    video_loop: bool = False
    roi_path: str = ""
    video_camera_id: str = ""
    video_role: str = ""
    retail_event_v1_enabled: bool = True

    @staticmethod
    def from_env() -> "VisionConfig":
        import os
        role_map_raw = os.getenv("VISION_ROLE_MAP", "{}")
        try:
            role_map = json.loads(role_map_raw)
        except Exception:
            role_map = {}
        return VisionConfig(
            enabled=os.getenv("VISION_ENABLED", "0") == "1",
            source=os.getenv("VISION_SOURCE", "rtsp").strip().lower() or "rtsp",
            bucket_seconds=int(os.getenv("VISION_BUCKET_SECONDS", "30")),
            poll_seconds=int(os.getenv("VISION_POLL_SECONDS", "5")),
            max_cameras=int(os.getenv("VISION_MAX_CAMERAS", "10")),
            snapshot_timeout_seconds=int(os.getenv("VISION_SNAPSHOT_TIMEOUT_SECONDS", "10")),
            role_map=role_map if isinstance(role_map, dict) else {},
            alerts_enabled=os.getenv("VISION_ALERTS_ENABLED", "0") == "1",
            inactivity_seconds=int(os.getenv("VISION_INACTIVITY_SECONDS", "120")),
            inactivity_cooldown_seconds=int(os.getenv("VISION_INACTIVITY_COOLDOWN_SECONDS", "300")),
            queue_size_threshold=int(os.getenv("VISION_QUEUE_SIZE_THRESHOLD", "3")),
            queue_wait_seconds=int(os.getenv("VISION_QUEUE_WAIT_SECONDS", "60")),
            queue_cooldown_seconds=int(os.getenv("VISION_QUEUE_COOLDOWN_SECONDS", "180")),
            phone_enabled=os.getenv("VISION_PHONE_ENABLED", "0") == "1",
            phone_seconds=int(os.getenv("VISION_PHONE_SECONDS", "30")),
            phone_cooldown_seconds=int(os.getenv("VISION_PHONE_COOLDOWN_SECONDS", "300")),
            phone_class_id=int(os.getenv("VISION_PHONE_CLASS_ID", "67")),
            blur_enabled=os.getenv("VISION_BLUR_ENABLED", "1") == "1",
            blur_strength=int(os.getenv("VISION_BLUR_STRENGTH", "41")),
            embed_thumbnail=os.getenv("VISION_EMBED_THUMBNAIL", "0") == "1",
            thumbnail_width=int(os.getenv("VISION_THUMBNAIL_WIDTH", "320")),
            frame_stride=max(1, int(os.getenv("VISION_FRAME_STRIDE", "1"))),
            video_path=os.getenv("VISION_VIDEO_PATH", "").strip(),
            video_realtime=os.getenv("VISION_VIDEO_REALTIME", "0") == "1",
            video_loop=os.getenv("VISION_VIDEO_LOOP", "0") == "1",
            roi_path=os.getenv("VISION_ROI_PATH", "").strip(),
            video_camera_id=os.getenv("VISION_CAMERA_ID", "").strip(),
            video_role=os.getenv("VISION_ROLE", "").strip().lower(),
            retail_event_v1_enabled=os.getenv("VISION_RETAIL_EVENT_V1_ENABLED", "1") == "1",
        )


class VisionWorker:
    def __init__(self, *, cloud_base_url: str, store_id: str, edge_token: str, logger):
        self.cloud_base_url = cloud_base_url.rstrip("/")
        self.store_id = store_id
        self.edge_token = edge_token
        self.logger = logger
        self.cfg = VisionConfig.from_env()
        self._stop = threading.Event()

        self._camera_states: Dict[str, dict] = {}
        self._roi_override: Optional[dict] = None
        self._roi_cache: Dict[str, dict] = {}
        self._roi_path_by_camera: Dict[str, str] = {}
        self._outbox_enabled = self._parse_bool_env("VISION_OUTBOX_ENABLED", True)
        self._outbox_batch_size = max(1, int(_env_str("VISION_OUTBOX_BATCH_SIZE", "50") or "50"))
        self._outbox_max_attempts = max(1, int(_env_str("VISION_OUTBOX_MAX_ATTEMPTS", "8") or "8"))
        self._outbox = VisionOutbox(self._resolve_outbox_path()) if self._outbox_enabled else None
        self._last_outbox_log_at = 0.0
        if self.cfg.roi_path:
            try:
                zones, lines = load_roi_yaml(self.cfg.roi_path)
                self._roi_override = {"zones": zones, "lines": lines}
                self.logger.info("[VISION] ROI override loaded from %s", self.cfg.roi_path)
                for name, pts in zones.items():
                    self.logger.info("[VISION] ROI zone=%s points=%s", name, len(pts))
                for name, pts in lines.items():
                    self.logger.info("[VISION] ROI line=%s points=%s", name, len(pts))
            except Exception as exc:
                self.logger.warning("[VISION] ROI override failed: %s", exc)
                self._roi_override = None

    def stop(self):
        self._stop.set()

    def run_forever(self):
        if not self.cfg.enabled:
            self.logger.info("[VISION] disabled (VISION_ENABLED=0)")
            return
        self._log_startup_info()
        if self.cfg.source == "video":
            self._run_video_forever()
            return
        self.logger.info("[VISION] worker started (bucket=%ss)", self.cfg.bucket_seconds)
        while not self._stop.is_set():
            try:
                self._flush_outbox()
                self.tick_once()
                self._flush_outbox()
            except Exception as exc:
                self.logger.exception("[VISION] tick failed: %s", exc)
            time.sleep(self.cfg.poll_seconds)

    def tick_once(self):
        cameras = self._fetch_cameras()
        if not cameras:
            return

        now = _now_ts()
        bucket_start = _bucket_start(now, self.cfg.bucket_seconds)

        processed = 0
        for cam in cameras[: self.cfg.max_cameras]:
            cam_id = str(cam.get("camera_id") or cam.get("id") or "").strip()
            if not cam_id:
                continue
            role = self._resolve_role(cam)
            if not role:
                continue
            state = self._camera_states.setdefault(cam_id, self._init_camera_state(role))

            frame = self._fetch_rtsp_frame(cam)
            if frame is None:
                frame = self._fetch_snapshot_frame(cam)
            if frame is None:
                self.logger.info("[VISION] snapshot missing camera_id=%s", cam_id)
                continue

            metrics = self._process_frame(state, cam, frame, now)
            if metrics is None:
                continue

            if state["bucket_start"] is None:
                state["bucket_start"] = bucket_start
            if bucket_start != state["bucket_start"]:
                payload = self._build_payload(cam, state, metrics, state["bucket_start"], bucket_start)
                self._log_bucket_summary(payload, state)
                self._send_event(payload)
                state["bucket_start"] = bucket_start
                state["agg"] = self._fresh_agg()
            processed += 1

        if processed:
            self.logger.info("[VISION] tick processed=%s bucket_start=%s", processed, bucket_start)

    def _init_camera_state(self, role: str) -> dict:
        return {
            "role": role,
            "bucket_start": None,
            "agg": self._fresh_agg(),
            "track_line_side_state": {},
            "track_line_last_event": {},
            "room_track_enter_ts": {},
            "room_track_last_seen_ts": {},
            "checkout_cycle": {"in_cycle": False, "interaction_start": None, "last_checkout": -1e9},
            "model": None,
            "idle_start_ts": None,
            "queue_start_ts": None,
            "phone_start_ts": None,
            "last_alert_ts": {},
            "roi_lines_count": 0,
        }

    def _fresh_agg(self) -> dict:
        return {
            "frames": 0,
            "frames_processed_for_detection": 0,
            "frames_with_detections": 0,
            "detections_sum": 0,
            "line_crossings_count": 0,
            "fila_sum": 0,
            "fila_max": 0,
            "consumo_sum": 0,
            "consumo_max": 0,
            "consumo_dwell_sum": 0,
            "consumo_dwell_samples": 0,
            "entries": 0,
            "exits": 0,
            "checkout_events": 0,
            "staff_active_est": 0,
        }

    def _run_video_forever(self) -> None:
        if not self.cfg.video_path:
            self.logger.warning("[VISION] video source selected but VISION_VIDEO_PATH is empty")
            return
        cam = self._build_video_camera()
        if cam is None:
            self.logger.warning("[VISION] video source missing role or ROI; skipping")
            return
        role = cam.get("role")
        if not role:
            self.logger.warning("[VISION] video source missing role; skipping")
            return
        state = self._init_camera_state(role)
        source = VideoFrameSource(
            path=self.cfg.video_path,
            realtime=self.cfg.video_realtime,
            loop=self.cfg.video_loop,
            logger=self.logger,
        )
        last_ts: Optional[float] = None
        try:
            for frame, ts in source.frames():
                if self._stop.is_set():
                    break
                self._flush_outbox(limit=10)
                last_ts = ts
                bucket_start = _bucket_start(ts, self.cfg.bucket_seconds)
                metrics = self._process_frame(state, cam, frame, ts)
                if metrics is None:
                    continue
                if state["bucket_start"] is None:
                    state["bucket_start"] = bucket_start
                if bucket_start != state["bucket_start"]:
                    payload = self._build_payload(cam, state, metrics, state["bucket_start"], bucket_start)
                    self._log_bucket_summary(payload, state)
                    self._send_event(payload)
                    state["bucket_start"] = bucket_start
                    state["agg"] = self._fresh_agg()
        except Exception as exc:
            self.logger.warning("[VISION] video loop failed: %s", exc)

        if last_ts is not None and state["bucket_start"] is not None:
            bucket_end = state["bucket_start"] + self.cfg.bucket_seconds
            payload = self._build_payload(cam, state, {}, state["bucket_start"], bucket_end)
            self._log_bucket_summary(payload, state)
            self._send_event(payload)
        self._flush_outbox()

    def _resolve_outbox_path(self) -> Path:
        raw = _env_str("VISION_OUTBOX_PATH", "").strip()
        if raw:
            path = Path(raw)
            if not path.is_absolute():
                path = Path.cwd() / path
            return path
        return Path.cwd() / "cache" / "vision_outbox.sqlite"

    def _outbox_backoff_seconds(self, attempts: int) -> int:
        return min(300, int(2 ** min(max(1, attempts), 8)))

    def _send_now(self, envelope: dict) -> tuple[bool, Optional[int], Optional[str]]:
        url = f"{self.cloud_base_url}/api/edge/events/"
        headers = build_auth_headers(self.edge_token)
        try:
            resp = requests.post(url, json=envelope, headers=headers, timeout=10)
            if 200 <= resp.status_code < 300:
                return True, resp.status_code, None
            detail = None
            try:
                body = resp.json()
                detail = body.get("detail") if isinstance(body, dict) else str(body)
            except Exception:
                detail = (resp.text or "").strip()[:300]
            return False, resp.status_code, detail or f"http_{resp.status_code}"
        except Exception as exc:
            return False, None, str(exc)

    def _send_or_enqueue(self, *, envelope: dict, context: str) -> None:
        ok, status, error = self._send_now(envelope)
        receipt = str(envelope.get("receipt_id") or "")[:10]
        if ok:
            self.logger.info("[VISION] %s sent status=%s receipt=%s", context, status, receipt)
            return
        if self._outbox is None:
            self.logger.warning("[VISION] %s send failed status=%s error=%s", context, status, error)
            return
        queued = self._outbox.enqueue(envelope)
        self.logger.warning(
            "[VISION] %s send failed status=%s error=%s queued=%s receipt=%s",
            context,
            status,
            error,
            queued,
            receipt,
        )

    def _flush_outbox(self, *, limit: Optional[int] = None) -> None:
        if self._outbox is None:
            return
        batch_size = int(limit or self._outbox_batch_size)
        batch = self._outbox.peek_batch(limit=batch_size)
        if not batch:
            return
        sent = 0
        failed = 0
        dropped = 0
        for row_id, payload, attempts in batch:
            ok, status, error = self._send_now(payload)
            if ok:
                self._outbox.mark_sent(row_id)
                sent += 1
                continue
            next_attempts = int(attempts) + 1
            if next_attempts >= self._outbox_max_attempts:
                self._outbox.mark_sent(row_id)
                dropped += 1
                self.logger.error(
                    "[VISION] outbox drop row=%s attempts=%s status=%s error=%s",
                    row_id,
                    next_attempts,
                    status,
                    error,
                )
                continue
            self._outbox.mark_failed(
                row_id,
                attempts=next_attempts,
                error=str(error or f"http_{status or 'error'}"),
                backoff_seconds=self._outbox_backoff_seconds(next_attempts),
            )
            failed += 1

        now = time.time()
        if sent or failed or dropped or (now - self._last_outbox_log_at) > 60:
            pending = self._outbox.size()
            oldest_pending_seconds = self._outbox.oldest_pending_seconds()
            self.logger.info(
                "[VISION] outbox flush sent=%s failed=%s dropped=%s pending=%s oldest_pending_seconds=%s",
                sent,
                failed,
                dropped,
                pending,
                oldest_pending_seconds,
            )
            self._last_outbox_log_at = now

    def _parse_bool_env(self, name: str, default: bool) -> bool:
        raw = _env_str(name, "")
        if not raw:
            return default
        value = raw.strip().lower()
        if value in {"1", "true", "yes", "y", "on"}:
            return True
        if value in {"0", "false", "no", "n", "off"}:
            return False
        self.logger.warning("[VISION] invalid boolean env %s=%s using default=%s", name, raw, default)
        return default

    def _cameras_cache_path(self) -> Path:
        raw = _env_str("VISION_CAMERAS_CACHE_PATH", "").strip()
        if raw:
            return Path(raw)
        return Path.cwd() / "cache" / "cameras_cache.json"

    def _parse_cameras_json(self, raw: str, *, source: str) -> tuple[list[dict], Optional[str]]:
        if not raw.strip():
            return [], None
        try:
            payload = json.loads(raw)
        except Exception as exc:
            return [], f"{source} invalid JSON: {exc}"
        if not isinstance(payload, list):
            return [], f"{source} must be a JSON array"
        cameras: list[dict] = []
        for idx, item in enumerate(payload):
            normalized = self._normalize_camera(item)
            if normalized is None:
                self.logger.warning("[VISION] %s item=%s skipped (missing id/frame source)", source, idx)
                continue
            cameras.append(normalized)
        return cameras, None

    def _load_cameras_json_from_env_file(self) -> str:
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            return ""
        try:
            raw_text = env_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_text = env_path.read_text(encoding="latin-1")
        try:
            values = dotenv_values(stream=io.StringIO(raw_text))
        except Exception as exc:
            self.logger.warning("[VISION] env fallback parse failed path=%s error=%s", env_path, exc)
            return ""
        raw = str(values.get("CAMERAS_JSON") or "").strip()
        if raw:
            self.logger.info("[VISION] CAMERAS_JSON loaded from .env fallback path=%s len=%s", env_path, len(raw))
        return raw

    def _normalize_camera(self, cam: Any) -> Optional[dict]:
        if not isinstance(cam, dict):
            return None
        camera_id = str(cam.get("camera_id") or cam.get("id") or "").strip()
        rtsp_url = str(
            cam.get("rtsp_url")
            or cam.get("stream_url")
            or cam.get("rtsp")
            or cam.get("url")
            or ""
        ).strip()
        snapshot_url = str(
            cam.get("last_snapshot_url")
            or cam.get("snapshot_url")
            or cam.get("snapshot")
            or ""
        ).strip()
        if not camera_id or (not rtsp_url and not snapshot_url):
            return None
        return {
            **cam,
            "id": camera_id,
            "camera_id": camera_id,
            "rtsp_url": rtsp_url,
            "last_snapshot_url": snapshot_url,
            "name": str(cam.get("name") or "").strip(),
            "external_id": str(cam.get("external_id") or cam.get("name") or "").strip(),
        }

    def _canonical_shape_name(self, name: str) -> str:
        value = _slug(name)
        if not value:
            return ""
        if "funcionario" in value and "caixa" in value:
            return "zona_funcionario_caixa"
        if "pagamento" in value or "caixa" in value:
            return "ponto_pagamento"
        if "fila" in value or "espera" in value:
            return "area_atendimento_fila"
        if "consumo" in value or "salao" in value or "sala" in value or "mesa" in value:
            return "area_consumo"
        if "entrada" in value or "saida" in value or "porta" in value:
            return "entrada"
        return value.replace(" ", "_")

    def _normalize_remote_roi_config(self, config_json: Any) -> Optional[dict]:
        if not isinstance(config_json, dict):
            return None
        zones_raw = config_json.get("zones") or []
        lines_raw = config_json.get("lines") or []
        normalized_zones: list[dict[str, Any]] = []
        normalized_lines: list[dict[str, Any]] = []

        if isinstance(zones_raw, list):
            for item in zones_raw:
                if not isinstance(item, dict):
                    continue
                pts = item.get("points") or []
                if not isinstance(pts, list) or not pts:
                    continue
                name = self._canonical_shape_name(str(item.get("name") or ""))
                if not name:
                    continue
                normalized_zones.append({**item, "name": name})

        if isinstance(lines_raw, list):
            for item in lines_raw:
                if not isinstance(item, dict):
                    continue
                pts = item.get("points") or []
                if not isinstance(pts, list) or len(pts) != 2:
                    continue
                name = self._canonical_shape_name(str(item.get("name") or ""))
                if not name:
                    continue
                normalized_lines.append({**item, "name": name})

        if not normalized_zones and not normalized_lines:
            return None

        roi_version = config_json.get("roi_version")
        return {
            **config_json,
            "zones": normalized_zones,
            "lines": normalized_lines,
            "roi_version": roi_version,
        }

    def _fetch_remote_roi_config(self, camera_id: str) -> Optional[dict]:
        payload, roi_version, _cached, error = fetch_roi(
            camera_id,
            cloud_base_url=self.cloud_base_url,
            edge_token=self.edge_token,
            logger=self.logger,
        )
        if payload is None:
            if error:
                self.logger.warning("[VISION] remote ROI unavailable camera_id=%s error=%s", camera_id, error)
            return None
        config_json = payload.get("config_json") if isinstance(payload, dict) else None
        normalized = self._normalize_remote_roi_config(config_json)
        if normalized is None:
            return None
        if roi_version and not normalized.get("roi_version"):
            normalized["roi_version"] = roi_version
        return normalized

    def _apply_roi_to_cameras(self, cameras: List[dict]) -> List[dict]:
        if self._roi_override:
            if len(cameras) > 1:
                self.logger.warning(
                    "[VISION] ROI override active with %s cameras; applying to all",
                    len(cameras),
                )
            for cam in cameras:
                cam["roi_local"] = self._roi_override
            return cameras

        for cam in cameras:
            camera_id = str(cam.get("camera_id") or cam.get("id") or "").strip()
            if not camera_id:
                continue
            local_roi = self._load_roi_for_camera(camera_id)
            cam["roi_local"] = local_roi
            if (local_roi.get("zones") or local_roi.get("lines")):
                continue
            remote_roi = self._fetch_remote_roi_config(camera_id)
            if remote_roi is not None:
                cam["roi"] = remote_roi
        return cameras

    def _save_cameras_cache(self, cameras: List[dict], *, source: str) -> None:
        path = self._cameras_cache_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "source": source,
                "updated_at": _iso(_now_ts()),
                "cameras": cameras,
            }
            path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        except Exception as exc:
            self.logger.warning("[VISION] cameras cache write failed path=%s error=%s", path, exc)

    def _load_cameras_cache(self) -> tuple[list[dict], Optional[str]]:
        path = self._cameras_cache_path()
        if not path.exists():
            return [], None
        try:
            raw = path.read_text(encoding="utf-8")
            payload = _safe_json_load(raw)
            if isinstance(payload, dict):
                cached_source = str(payload.get("source") or "cache")
                raw_cameras = payload.get("cameras")
            else:
                cached_source = "cache_legacy"
                raw_cameras = payload
            if not isinstance(raw_cameras, list):
                return [], None
            cameras = []
            for item in raw_cameras:
                normalized = self._normalize_camera(item)
                if normalized is not None:
                    cameras.append(normalized)
            return cameras, cached_source
        except Exception as exc:
            self.logger.warning("[VISION] cameras cache read failed path=%s error=%s", path, exc)
            return [], None

    def _fetch_cameras_from_edge(self) -> tuple[list[dict], Optional[str]]:
        headers = build_auth_headers(self.edge_token)
        for endpoint in EDGE_CAMERA_ENDPOINTS:
            path = endpoint.format(store_id=self.store_id)
            url = f"{self.cloud_base_url}{path}"
            params = {"store_id": self.store_id} if "{store_id}" not in endpoint else None
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                if resp.status_code >= 300:
                    if resp.status_code in (401, 403):
                        self.logger.warning(
                            "[VISION] cameras edge auth failed status=%s url=%s",
                            resp.status_code,
                            url,
                        )
                    else:
                        self.logger.warning("[VISION] cameras edge failed %s url=%s", resp.status_code, url)
                    continue
                payload = resp.json()
                raw_cameras = payload.get("results") if isinstance(payload, dict) else payload
                if isinstance(payload, dict) and raw_cameras is None:
                    raw_cameras = payload.get("data")
                if not isinstance(raw_cameras, list):
                    self.logger.warning("[VISION] cameras edge invalid payload url=%s", url)
                    continue
                cameras = []
                for item in raw_cameras:
                    normalized = self._normalize_camera(item)
                    if normalized is not None:
                        cameras.append(normalized)
                return cameras, f"edge:{path}"
            except Exception as exc:
                self.logger.warning("[VISION] cameras edge exception url=%s error=%s", url, exc)
        return [], None

    def _fetch_cameras(self) -> List[dict]:
        if self.cfg.source == "video":
            return []

        source_mode = str(_env_str("CAMERA_SOURCE_MODE", "api_first") or "api_first").strip().lower()
        local_only = self._parse_bool_env("VISION_LOCAL_CAMERAS_ONLY", False)
        if source_mode in {"local_only", "env_only"}:
            local_only = True
        elif source_mode not in {"api_first", ""}:
            self.logger.warning("[VISION] invalid CAMERA_SOURCE_MODE=%s fallback=api_first", source_mode)

        remote_sync_enabled = self._parse_bool_env("VISION_REMOTE_CAMERA_SYNC_ENABLED", True)
        camera_sync_enabled = self._parse_bool_env("CAMERA_SYNC_ENABLED", True)

        cameras_json_raw = _env_str("CAMERAS_JSON", "")
        if not cameras_json_raw.strip():
            cameras_json_raw = self._load_cameras_json_from_env_file()
        cameras_from_env, env_error = self._parse_cameras_json(cameras_json_raw, source="CAMERAS_JSON")
        if env_error:
            self.logger.warning("[VISION] %s", env_error)

        if camera_sync_enabled and remote_sync_enabled and not local_only:
            edge_cameras, edge_source = self._fetch_cameras_from_edge()
            if edge_cameras:
                cameras = self._apply_roi_to_cameras(edge_cameras)
                self._save_cameras_cache(cameras, source=edge_source or "edge")
                self.logger.info("[VISION] cameras source=%s loaded=%s", edge_source or "edge", len(cameras))
                return cameras
            self.logger.warning("[VISION] cameras edge sync unavailable; trying fallback")
        elif camera_sync_enabled and not remote_sync_enabled and not local_only:
            self.logger.info("[VISION] remote camera sync disabled for vision (VISION_REMOTE_CAMERA_SYNC_ENABLED=0)")
        elif not camera_sync_enabled and not local_only:
            self.logger.info("[VISION] cameras sync disabled (CAMERA_SYNC_ENABLED=0); using fallback")

        if cameras_from_env:
            cameras = self._apply_roi_to_cameras(cameras_from_env)
            self._save_cameras_cache(cameras, source="CAMERAS_JSON")
            self.logger.info("[VISION] cameras source=CAMERAS_JSON loaded=%s", len(cameras))
            return cameras

        if local_only:
            self.logger.warning("[VISION] local cameras only enabled and CAMERAS_JSON empty; loaded=0")
            return []

        cached_cameras, cached_source = self._load_cameras_cache()
        if cached_cameras:
            cameras = self._apply_roi_to_cameras(cached_cameras)
            self.logger.info("[VISION] cameras source=cache(%s) loaded=%s", cached_source or "cache", len(cameras))
            return cameras

        self.logger.warning("[VISION] cameras unavailable source=none loaded=0")
        return []

    def _resolve_role(self, cam: dict) -> Optional[str]:
        if cam.get("role"):
            return str(cam.get("role"))
        roi = cam.get("roi")
        if isinstance(roi, dict):
            zones = {}
            for item in roi.get("zones") or []:
                if not isinstance(item, dict):
                    continue
                name = self._canonical_shape_name(str(item.get("name") or ""))
                pts = item.get("points") or []
                if name and pts:
                    zones[name] = pts
            lines = {}
            for item in roi.get("lines") or []:
                if not isinstance(item, dict):
                    continue
                name = self._canonical_shape_name(str(item.get("name") or ""))
                pts = item.get("points") or []
                if name and len(pts) == 2:
                    lines[name] = pts
            inferred = self._infer_role_from_roi(zones, lines)
            if inferred:
                return inferred
        name = str(cam.get("name") or "").lower()
        ext = str(cam.get("external_id") or "").lower()
        if "caixa" in name or "caixa" in ext or "checkout" in name or "checkout" in ext:
            return "balcao"
        for role, key in self.cfg.role_map.items():
            if not key:
                continue
            if key.lower() in name or key.lower() in ext:
                return role
        for role in ("balcao", "salao", "entrada"):
            if role in name or role in ext:
                return role
        return None

    def _fetch_snapshot_frame(self, cam: dict):
        snapshot_url = cam.get("last_snapshot_url")
        if not snapshot_url:
            return None
        try:
            resp = requests.get(snapshot_url, timeout=self.cfg.snapshot_timeout_seconds)
            if resp.status_code >= 300:
                return None
            import numpy as np
            import cv2
            data = np.frombuffer(resp.content, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def _fetch_rtsp_frame(self, cam: dict):
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        rtsp_url = cam.get("rtsp_url")
        if not rtsp_url:
            self.logger.info("[VISION] rtsp attempt camera_id=%s ok=0 elapsed_ms=0 reason=rtsp_url_missing", camera_id)
            return None
        rtsp_url = str(rtsp_url)
        started = time.perf_counter()
        try:
            import cv2
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                self.logger.info("[VISION] rtsp attempt camera_id=%s ok=0 elapsed_ms=%s reason=open_failed", camera_id, elapsed_ms)
                self._log_ffmpeg_open_failed(camera_id=camera_id, rtsp_url=rtsp_url)
                return None
            ok, frame = cap.read()
            cap.release()
            if not ok:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                self.logger.info("[VISION] rtsp attempt camera_id=%s ok=0 elapsed_ms=%s reason=read_failed", camera_id, elapsed_ms)
                return None
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self.logger.info("[VISION] rtsp attempt camera_id=%s ok=1 elapsed_ms=%s", camera_id, elapsed_ms)
            return frame
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            self.logger.info(
                "[VISION] rtsp attempt camera_id=%s ok=0 elapsed_ms=%s reason=exception error=%s",
                camera_id,
                elapsed_ms,
                exc,
            )
            return None

    def _log_ffmpeg_open_failed(self, *, camera_id: str, rtsp_url: str) -> None:
        ffmpeg_path = _ffmpeg_path()
        if not ffmpeg_path:
            self.logger.info("[VISION] rtsp open_failed ffmpeg_not_found camera_id=%s", camera_id)
            return
        transport = _env_str("VISION_RTSP_TRANSPORT", "tcp").strip() or "tcp"
        try:
            timeout_seconds = int(_env_str("VISION_RTSP_DIAG_TIMEOUT_SECONDS", "8"))
        except Exception:
            timeout_seconds = 8
        timeout_seconds = max(3, timeout_seconds)
        stimeout_us = timeout_seconds * 1_000_000
        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-nostdin",
            "-rtsp_transport",
            transport,
            "-stimeout",
            str(stimeout_us),
            "-i",
            rtsp_url,
            "-t",
            "1",
            "-f",
            "null",
            "-",
        ]
        safe_cmd = cmd.copy()
        safe_cmd[safe_cmd.index(rtsp_url)] = mask_rtsp_url(rtsp_url)
        self.logger.info(
            "[VISION] rtsp open_failed ffmpeg_cmd camera_id=%s cmd=%s",
            camera_id,
            subprocess.list2cmdline(safe_cmd),
        )
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            stderr = _redact_rtsp_secrets((exc.stderr or "").strip(), rtsp_url)
            self.logger.info(
                "[VISION] rtsp open_failed ffmpeg timeout camera_id=%s timeout_s=%s",
                camera_id,
                timeout_seconds,
            )
            if stderr:
                self.logger.info(
                    "[VISION] rtsp open_failed ffmpeg stderr camera_id=%s\n%s",
                    camera_id,
                    stderr,
                )
            return
        stderr = _redact_rtsp_secrets((result.stderr or "").strip(), rtsp_url)
        if stderr:
            self.logger.info(
                "[VISION] rtsp open_failed ffmpeg stderr camera_id=%s exit_code=%s\n%s",
                camera_id,
                result.returncode,
                stderr,
            )
        else:
            self.logger.info(
                "[VISION] rtsp open_failed ffmpeg stderr camera_id=%s exit_code=%s <empty>",
                camera_id,
                result.returncode,
            )

    def _process_frame(self, state: dict, cam: dict, frame, ts: float) -> Optional[dict]:
        role = state["role"]
        agg = state["agg"]
        agg["frames"] += 1

        stride = max(1, int(self.cfg.frame_stride))
        if (agg["frames"] - 1) % stride != 0:
            return None

        agg["frames_processed_for_detection"] += 1
        roi = self._extract_roi(cam, frame)
        if roi is None:
            return None

        state["last_roi_context"] = roi
        zones = roi["zones"]
        lines = roi["lines"]
        state["roi_lines_count"] = len(lines)

        results = self._yolo_track(state, frame)
        fila_count = 0
        consumo_count = 0
        clients_at_pay = 0
        staff_at_cashier = 0
        consumo_dwell_seconds = 0

        phone_in_staff_zone = False
        people_detections = 0
        active_room_tracks = set()
        if results and results.get("boxes"):
            for item in results["boxes"]:
                if len(item) >= 6:
                    x1, y1, x2, y2, cls, track_id = item
                else:
                    x1, y1, x2, y2, cls = item
                    track_id = None
                is_person = cls == 0
                is_phone = cls == self.cfg.phone_class_id
                if not is_person and not is_phone:
                    continue
                if is_person:
                    people_detections += 1
                cx = int((x1 + x2) / 2)
                foot_y = int(y2)
                center_y = int((y1 + y2) / 2)

                if role == "balcao":
                    if is_phone and self.cfg.phone_enabled:
                        if "zona_funcionario_caixa" in zones and point_in_polygon(
                            cx, center_y, zones["zona_funcionario_caixa"]
                        ):
                            phone_in_staff_zone = True
                        continue
                    if not is_person:
                        continue
                    in_pay = "ponto_pagamento" in zones and point_in_polygon(cx, center_y, zones["ponto_pagamento"])
                    if in_pay:
                        clients_at_pay += 1
                    if "zona_funcionario_caixa" in zones and point_in_polygon(cx, center_y, zones["zona_funcionario_caixa"]):
                        staff_at_cashier += 1
                    if "area_atendimento_fila" in zones and point_in_polygon(cx, foot_y, zones["area_atendimento_fila"]):
                        if not (in_pay and _env_str("EXCLUDE_PAY_FROM_QUEUE", "1") == "1"):
                            fila_count += 1
                elif role == "salao":
                    if not is_person:
                        continue
                    if "area_consumo" in zones and point_in_polygon(cx, foot_y, zones["area_consumo"]):
                        consumo_count += 1
                        if track_id is not None:
                            room_enter_ts = state["room_track_enter_ts"]
                            room_last_seen_ts = state["room_track_last_seen_ts"]
                            if track_id not in room_enter_ts:
                                room_enter_ts[track_id] = ts
                            room_last_seen_ts[track_id] = ts
                            active_room_tracks.add(track_id)
                elif role == "entrada":
                    if not is_person or track_id is None:
                        continue
                    track_state = state["track_line_side_state"].setdefault(track_id, {})
                    track_events = state["track_line_last_event"].setdefault(track_id, {})
                    line_meta = (roi.get("line_meta") or {}) if isinstance(roi, dict) else {}
                    for line_name, pts in lines.items():
                        p1, p2 = pts
                        side = line_side(tuple(p1), tuple(p2), (cx, foot_y))
                        prev = track_state.get(line_name)
                        if prev is not None:
                            crossed_entry = prev < 0 <= side
                            crossed_exit = prev > 0 >= side
                            if crossed_entry:
                                key = f"entry:{line_name}"
                                last_t = float(track_events.get(key, -1e9))
                                if (ts - last_t) >= 4.0:
                                    agg["entries"] += 1
                                    agg["line_crossings_count"] += 1
                                    track_events[key] = ts
                                    self._send_crossing_event(
                                        cam=cam,
                                        line_name=line_name,
                                        line_meta=line_meta.get(line_name) or {},
                                        direction="entry",
                                        ts=ts,
                                        track_id=track_id,
                                    )
                            elif crossed_exit:
                                key = f"exit:{line_name}"
                                last_t = float(track_events.get(key, -1e9))
                                if (ts - last_t) >= 4.0:
                                    agg["exits"] += 1
                                    agg["line_crossings_count"] += 1
                                    track_events[key] = ts
                                    self._send_crossing_event(
                                        cam=cam,
                                        line_name=line_name,
                                        line_meta=line_meta.get(line_name) or {},
                                        direction="exit",
                                        ts=ts,
                                        track_id=track_id,
                                    )
                        track_state[line_name] = side

        if role == "salao":
            room_enter_ts = state.get("room_track_enter_ts") or {}
            room_last_seen_ts = state.get("room_track_last_seen_ts") or {}
            dwell_values = []
            for track_id in active_room_tracks:
                enter_ts = float(room_enter_ts.get(track_id) or ts)
                dwell_values.append(max(0, int(round(ts - enter_ts))))
            consumo_dwell_seconds = int(round(sum(dwell_values) / len(dwell_values))) if dwell_values else 0

            stale_after_seconds = max(10, int(self.cfg.poll_seconds) * 3)
            stale_track_ids = [
                track_id
                for track_id, last_seen in room_last_seen_ts.items()
                if (ts - float(last_seen or ts)) >= stale_after_seconds
            ]
            for track_id in stale_track_ids:
                room_enter_ts.pop(track_id, None)
                room_last_seen_ts.pop(track_id, None)

        agg = state["agg"]
        agg["detections_sum"] += people_detections
        if people_detections > 0:
            agg["frames_with_detections"] += 1
        if agg["frames"] % 30 == 0:
            camera_id = str(cam.get("camera_id") or cam.get("id") or "")
            self.logger.info(
                "[VISION] detections camera_id=%s frames=%s people_detections=%s",
                camera_id,
                agg["frames"],
                people_detections,
            )
        if role == "balcao":
            agg["fila_sum"] += fila_count
            agg["fila_max"] = max(agg["fila_max"], fila_count)
            agg["staff_active_est"] = max(agg["staff_active_est"], staff_at_cashier)
            self._send_queue_state_event(
                cam=cam,
                roi=roi,
                queue_length=fila_count,
                staff_active_est=staff_at_cashier,
                ts=ts,
            )
            self._track_checkout_cycle(
                state=state,
                cam=cam,
                roi=roi,
                clients_at_pay=clients_at_pay,
                staff_active=staff_at_cashier,
                ts=ts,
            )
        if role == "salao":
            agg["consumo_sum"] += consumo_count
            agg["consumo_max"] = max(agg["consumo_max"], consumo_count)
            if consumo_dwell_seconds > 0:
                agg["consumo_dwell_sum"] += consumo_dwell_seconds
                agg["consumo_dwell_samples"] += 1
            self._send_zone_occupancy_event(
                cam=cam,
                roi=roi,
                occupancy_count=consumo_count,
                dwell_seconds_est=consumo_dwell_seconds,
                ts=ts,
            )

        if self.cfg.alerts_enabled and role == "balcao":
            self._handle_alerts(
                state=state,
                cam=cam,
                ts=ts,
                fila_count=fila_count,
                staff_active=staff_at_cashier,
                clients_at_pay=clients_at_pay,
                phone_in_staff_zone=phone_in_staff_zone,
                frame=frame,
            )

        return {
            "fila_count": fila_count,
            "consumo_count": consumo_count,
            "staff_active": staff_at_cashier,
            "entries": int(agg.get("entries") or 0),
            "exits": int(agg.get("exits") or 0),
        }

    def _handle_alerts(
        self,
        *,
        state: dict,
        cam: dict,
        ts: float,
        fila_count: int,
        staff_active: int,
        clients_at_pay: int,
        phone_in_staff_zone: bool,
        frame,
    ) -> None:
        now_ts = ts
        last_alert_ts = state["last_alert_ts"]

        idle_start = state.get("idle_start_ts")
        if staff_active >= 1 and fila_count == 0 and clients_at_pay == 0:
            if idle_start is None:
                state["idle_start_ts"] = now_ts
            idle_duration = now_ts - (state["idle_start_ts"] or now_ts)
            if idle_duration >= self.cfg.inactivity_seconds:
                if self._cooldown_ok(last_alert_ts, "employee_inactivity", self.cfg.inactivity_cooldown_seconds, now_ts):
                    self._emit_alert(
                        cam=cam,
                        event_type="employee_inactivity",
                        severity="warning",
                        title="Ociosidade detectada",
                        description=f"Equipe ociosa por {int(idle_duration)}s.",
                        metadata={"duration_seconds": int(idle_duration), "staff_active_est": staff_active},
                        ts=now_ts,
                        frame=frame,
                    )
                    last_alert_ts["employee_inactivity"] = now_ts
        else:
            state["idle_start_ts"] = None

        queue_start = state.get("queue_start_ts")
        if fila_count >= self.cfg.queue_size_threshold:
            if queue_start is None:
                state["queue_start_ts"] = now_ts
            queue_duration = now_ts - (state["queue_start_ts"] or now_ts)
            if queue_duration >= self.cfg.queue_wait_seconds:
                if self._cooldown_ok(last_alert_ts, "queue_long", self.cfg.queue_cooldown_seconds, now_ts):
                    self._emit_alert(
                        cam=cam,
                        event_type="queue_long",
                        severity="warning",
                        title="Fila longa detectada",
                        description=f"Fila com {fila_count} pessoas por {int(queue_duration)}s.",
                        metadata={"queue_size": fila_count, "queue_wait_seconds": int(queue_duration)},
                        ts=now_ts,
                        frame=frame,
                    )
                    last_alert_ts["queue_long"] = now_ts
        else:
            state["queue_start_ts"] = None

        if self.cfg.phone_enabled:
            if phone_in_staff_zone:
                if state.get("phone_start_ts") is None:
                    state["phone_start_ts"] = now_ts
                phone_duration = now_ts - (state.get("phone_start_ts") or now_ts)
                if phone_duration >= self.cfg.phone_seconds:
                    if self._cooldown_ok(last_alert_ts, "phone_usage", self.cfg.phone_cooldown_seconds, now_ts):
                        self._emit_alert(
                            cam=cam,
                            event_type="phone_usage",
                            severity="warning",
                            title="Uso de celular detectado",
                            description=f"Uso de celular por ~{int(phone_duration)}s na zona de atendimento.",
                            metadata={"duration_seconds": int(phone_duration)},
                            ts=now_ts,
                            frame=frame,
                        )
                        last_alert_ts["phone_usage"] = now_ts
                        state["phone_start_ts"] = None
            else:
                state["phone_start_ts"] = None

    def _cooldown_ok(self, last_alert_ts: dict, key: str, cooldown: int, now_ts: float) -> bool:
        last_ts = float(last_alert_ts.get(key) or 0)
        return (now_ts - last_ts) >= cooldown

    def _emit_alert(
        self,
        *,
        cam: dict,
        event_type: str,
        severity: str,
        title: str,
        description: str,
        metadata: dict,
        ts: float,
        frame,
    ) -> None:
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        receipt_id = _sha256(f"{event_type}|{self.store_id}|{camera_id}|{int(ts)}")
        payload = {
            "store_id": self.store_id,
            "camera_id": camera_id,
            "event_type": event_type,
            "severity": severity,
            "title": title,
            "description": description,
            "metadata": metadata,
            "occurred_at": _iso(ts),
        }
        if self.cfg.embed_thumbnail and frame is not None:
            thumb = self._build_thumbnail(frame)
            if thumb:
                payload["metadata"] = {**metadata, "thumbnail_base64": thumb, "thumbnail_blurred": True}
        self._send_alert_event(payload, receipt_id=receipt_id)

    def _build_thumbnail(self, frame) -> Optional[str]:
        try:
            import cv2
            h, w = frame.shape[:2]
            if self.cfg.blur_enabled:
                k = max(3, int(self.cfg.blur_strength) | 1)
                frame = cv2.GaussianBlur(frame, (k, k), 0)
            target_w = max(160, self.cfg.thumbnail_width)
            scale = target_w / max(w, 1)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok:
                return None
            import base64
            return base64.b64encode(buffer.tobytes()).decode("utf-8")
        except Exception:
            return None

    def _send_alert_event(self, payload: dict, *, receipt_id: str):
        envelope = {
            "event_name": "alert",
            "event_type": payload.get("event_type"),
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload.get("occurred_at"),
            "data": payload,
        }
        self._send_or_enqueue(envelope=envelope, context=f"alert:{payload.get('event_type')}")

    def _yolo_track(self, state: dict, frame) -> Optional[dict]:
        try:
            from ultralytics import YOLO
            if state.get("model") is None:
                model_path = _env_str("VISION_MODEL_PATH", "").strip()
                if not model_path:
                    model_path = "yolov8n.pt"
                state["model"] = YOLO(model_path)
            res = state["model"].track(frame, persist=True, verbose=False, conf=0.35, iou=0.45)[0]
            if res.boxes is None:
                return None
            boxes = res.boxes.xyxy.cpu().numpy().astype(int)
            clss = res.boxes.cls.cpu().numpy().astype(int)
            track_ids = None
            if getattr(res.boxes, "id", None) is not None:
                track_ids = res.boxes.id.cpu().numpy().astype(int)
            items = []
            for idx, ((x1, y1, x2, y2), cls) in enumerate(zip(boxes, clss)):
                track_id = int(track_ids[idx]) if track_ids is not None and idx < len(track_ids) else None
                items.append([x1, y1, x2, y2, int(cls), track_id])
            return {"boxes": items}
        except Exception as exc:
            self.logger.warning("[VISION] yolo failed: %s", exc)
            return None

    def _infer_metric_type_from_name(self, name: str, shape_type: str) -> str:
        canonical = self._canonical_shape_name(name)
        if shape_type == "line":
            return "entry_exit"
        if canonical in {"area_atendimento_fila", "fila", "espera"}:
            return "queue"
        if canonical in {"ponto_pagamento", "caixa", "checkout"}:
            return "checkout_proxy"
        if canonical in {"area_consumo", "salao", "mesa"}:
            return "occupancy"
        return "custom"

    def _extract_roi(self, cam: dict, frame) -> Optional[dict]:
        camera_zone_id = cam.get("zone_id")
        roi_local = cam.get("roi_local") or {}
        if roi_local.get("zones") or roi_local.get("lines"):
            zones_raw = roi_local.get("zones") or {}
            lines_raw = roi_local.get("lines") or {}
            zones: Dict[str, List[List[int]]] = {}
            zone_meta: Dict[str, dict] = {}
            for name, pts in zones_raw.items():
                if not name or not pts:
                    continue
                zones[name] = [[int(p[0]), int(p[1])] for p in pts]
                zone_meta[name] = {
                    "zone_id": camera_zone_id,
                    "roi_entity_id": name,
                    "metric_type": self._infer_metric_type_from_name(name, "zone"),
                    "ownership": "primary",
                }
            lines: Dict[str, List[List[int]]] = {}
            line_meta: Dict[str, dict] = {}
            for name, pts in lines_raw.items():
                if not name or not pts or len(pts) != 2:
                    continue
                lines[name] = [[int(pts[0][0]), int(pts[0][1])], [int(pts[1][0]), int(pts[1][1])]]
                line_meta[name] = {
                    "zone_id": camera_zone_id,
                    "roi_entity_id": name,
                    "metric_type": self._infer_metric_type_from_name(name, "line"),
                    "ownership": "primary",
                }
            return {"zones": zones, "lines": lines, "zone_meta": zone_meta, "line_meta": line_meta}
        config_json = cam.get("roi") or {}
        if not isinstance(config_json, dict):
            return None
        zones_raw = config_json.get("zones") or []
        lines_raw = config_json.get("lines") or []

        h, w = frame.shape[:2]
        zones: Dict[str, List[List[int]]] = {}
        zone_meta: Dict[str, dict] = {}
        for z in zones_raw:
            name = z.get("name")
            pts = z.get("points") or []
            if not name or not pts:
                continue
            px = []
            for p in pts:
                px.append([int(p["x"] * w), int(p["y"] * h)])
            zones[name] = px
            zone_meta[name] = {
                "zone_id": z.get("zone_id") or camera_zone_id,
                "roi_entity_id": z.get("roi_entity_id") or z.get("id") or name,
                "metric_type": z.get("metric_type") or self._infer_metric_type_from_name(name, "zone"),
                "ownership": z.get("ownership") or "primary",
            }

        lines: Dict[str, List[List[int]]] = {}
        line_meta: Dict[str, dict] = {}
        for ln in lines_raw:
            name = ln.get("name")
            pts = ln.get("points") or []
            if not name or len(pts) != 2:
                continue
            p1 = [int(pts[0]["x"] * w), int(pts[0]["y"] * h)]
            p2 = [int(pts[1]["x"] * w), int(pts[1]["y"] * h)]
            lines[name] = [p1, p2]
            line_meta[name] = {
                "zone_id": ln.get("zone_id") or camera_zone_id,
                "roi_entity_id": ln.get("roi_entity_id") or ln.get("id") or name,
                "metric_type": ln.get("metric_type") or self._infer_metric_type_from_name(name, "line"),
                "ownership": ln.get("ownership") or "primary",
            }

        if not zones and not lines:
            return None
        return {"zones": zones, "lines": lines, "zone_meta": zone_meta, "line_meta": line_meta}

    def _build_video_camera(self) -> Optional[dict]:
        camera_id = self._get_video_camera_id()
        roi = self._roi_override or self._load_roi_for_camera(camera_id)
        role = self.cfg.video_role or self._infer_role_from_roi(roi.get("zones") or {}, roi.get("lines") or {})
        name = self.cfg.video_camera_id or self.cfg.video_path
        cam = {
            "camera_id": camera_id,
            "name": name,
            "external_id": name,
            "role": role,
            "roi_local": roi,
            "roi": {"roi_version": "local"},
        }
        return cam

    def _get_video_camera_id(self) -> str:
        return self.cfg.video_camera_id or _sha256(self.cfg.video_path)[:12]

    def _programdata_roi_path(self, camera_id: str) -> Path:
        import os
        program_data = os.getenv("PROGRAMDATA") or "C:\\ProgramData"
        base = Path(program_data) / "DaleVision" / "rois" / self.store_id
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{camera_id}.yaml"

    def _legacy_roi_path(self, camera_id: str) -> Path:
        return Path.cwd() / "edge-agent" / "config" / "rois" / f"{camera_id}.yaml"

    def _load_roi_for_camera(self, camera_id: str) -> dict:
        if not camera_id:
            return {"zones": {}, "lines": {}}
        if camera_id in self._roi_cache:
            return self._roi_cache[camera_id]

        candidates: List[Path] = []
        if self.cfg.roi_path:
            candidates.append(Path(self.cfg.roi_path))
        else:
            candidates.append(self._programdata_roi_path(camera_id))
            candidates.append(self._legacy_roi_path(camera_id))

        for path in candidates:
            try:
                if path.exists():
                    zones, lines = load_roi_yaml(str(path))
                    roi = {"zones": zones, "lines": lines}
                    self._roi_cache[camera_id] = roi
                    self._roi_path_by_camera[camera_id] = str(path)
                    self.logger.info(
                        "[VISION] ROI loaded camera_id=%s path=%s zones=%s lines=%s",
                        camera_id,
                        path,
                        len(zones),
                        len(lines),
                    )
                    return roi
            except Exception as exc:
                self.logger.warning("[VISION] ROI load failed camera_id=%s path=%s error=%s", camera_id, path, exc)

        effective_path = str(candidates[0]) if candidates else ""
        self._roi_path_by_camera[camera_id] = effective_path
        self.logger.warning("[VISION] ROI not found camera_id=%s; using empty ROI.", camera_id)
        roi = {"zones": {}, "lines": {}}
        self._roi_cache[camera_id] = roi
        return roi

    def _infer_role_from_roi(self, zones: dict, lines: dict) -> Optional[str]:
        zone_names = set(zones.keys())
        if {"area_atendimento_fila", "ponto_pagamento", "zona_funcionario_caixa"} & zone_names:
            return "balcao"
        if "area_consumo" in zone_names:
            return "salao"
        if lines:
            return "entrada"
        return None

    def _select_metric_context(
        self,
        roi: Optional[dict],
        *,
        entity_type: str,
        metric_type: str,
        fallback_zone_id: Optional[str],
    ) -> dict:
        if entity_type == "line":
            meta_map = (roi or {}).get("line_meta") or {}
        else:
            meta_map = (roi or {}).get("zone_meta") or {}
        values = [value for value in meta_map.values() if isinstance(value, dict)]
        matching = [value for value in values if value.get("metric_type") == metric_type]
        primary_matching = [value for value in matching if value.get("ownership") != "secondary"]
        primary_values = [value for value in values if value.get("ownership") != "secondary"]
        selected = None
        if primary_matching:
            selected = primary_matching[0]
        elif matching:
            selected = matching[0]
        elif primary_values:
            selected = primary_values[0]
        elif values:
            selected = values[0]
        selected = selected or {}
        return {
            "zone_id": selected.get("zone_id") or fallback_zone_id,
            "roi_entity_id": selected.get("roi_entity_id"),
            "metric_type": selected.get("metric_type") or metric_type,
            "ownership": selected.get("ownership") or "primary",
        }

    def _build_payload(self, cam: dict, state: dict, last_metrics: dict, bucket_start: int, bucket_end: int) -> dict:
        agg = state["agg"]
        frames = max(agg["frames"], 1)
        role = self.cfg.video_role or cam.get("role") or self._resolve_role(cam)
        roi = state.get("last_roi_context") or {}
        camera_zone_id = cam.get("zone_id")

        traffic_context = self._select_metric_context(
            roi,
            entity_type="line" if role == "entrada" else "zone",
            metric_type="entry_exit" if role == "entrada" else ("occupancy" if role == "salao" else "queue"),
            fallback_zone_id=camera_zone_id,
        )
        conversion_context = self._select_metric_context(
            roi,
            entity_type="zone",
            metric_type="checkout_proxy",
            fallback_zone_id=camera_zone_id,
        )

        payload = {
            "store_id": self.store_id,
            "camera_id": str(cam.get("camera_id") or cam.get("id") or ""),
            "camera_role": role or "unknown",
            "roi_version": (cam.get("roi") or {}).get("roi_version"),
            "bucket": {
                "seconds": self.cfg.bucket_seconds,
                "start": _iso(bucket_start),
                "end": _iso(bucket_end),
            },
            "ownership": {
                "mode": "single_camera_owner",
                "camera_id": str(cam.get("camera_id") or cam.get("id") or ""),
                "camera_role": role or "unknown",
            },
            "traffic": {
                "footfall": agg["entries"] if role == "entrada" else 0,
                "entries": int(agg.get("entries") or 0),
                "exits": int(agg.get("exits") or 0),
                "engaged": int(agg.get("consumo_max") or 0) if role == "salao" else 0,
                "dwell_seconds_avg": (
                    int((agg.get("consumo_dwell_sum") or 0) / max(1, int(agg.get("consumo_dwell_samples") or 0)))
                    if role == "salao" and int(agg.get("consumo_dwell_samples") or 0) > 0
                    else 0
                ),
                "zone_id": traffic_context.get("zone_id"),
                "roi_entity_id": traffic_context.get("roi_entity_id"),
                "metric_type": traffic_context.get("metric_type"),
            },
            "conversion": {
                "queue_avg_seconds": int(agg["fila_sum"] / frames) if frames else 0,
                "staff_active_est": int(agg["staff_active_est"]),
                "checkout_events": int(agg.get("checkout_events") or 0),
                "conversion_method": "checkout_proxy" if role == "balcao" else None,
                "zone_id": conversion_context.get("zone_id"),
                "roi_entity_id": conversion_context.get("roi_entity_id"),
                "metric_type": conversion_context.get("metric_type") if role == "balcao" else None,
            },
            "debug": {
                "frame_source": "rtsp_or_snapshot",
                "snapshot_url_present": bool(cam.get("last_snapshot_url")),
                "line_crossings_count": int(agg.get("line_crossings_count") or 0),
            },
        }
        return payload

    def _log_bucket_summary(self, payload: dict, state: dict) -> None:
        agg = state.get("agg") or {}
        bucket = payload.get("bucket") or {}
        bucket_start = bucket.get("start")
        bucket_end = bucket.get("end")
        bucket_seconds = bucket.get("seconds")
        camera_id = payload.get("camera_id")
        frames = agg.get("frames", 0)
        fila_max = agg.get("fila_max", 0)
        consumo_max = agg.get("consumo_max", 0)
        staff_active_est = agg.get("staff_active_est", 0)
        queue_avg_seconds = (payload.get("conversion") or {}).get("queue_avg_seconds", 0)
        frames_processed_for_detection = agg.get("frames_processed_for_detection", 0)
        stride = max(1, int(self.cfg.frame_stride))
        frames_with_detections = agg.get("frames_with_detections", 0)
        detections_sum = agg.get("detections_sum", 0)
        avg_detections = (detections_sum / frames) if frames else 0.0
        line_crossings = agg.get("line_crossings_count")
        line_crossings_str = "NA" if line_crossings is None else str(line_crossings)
        lines_defined_count = int(state.get("roi_lines_count") or 0)
        message = (
            f"[VISION] bucket camera_id={camera_id} start={bucket_start} end={bucket_end} "
            f"seconds={bucket_seconds} frames={frames} fila_max={fila_max} "
            f"consumo_max={consumo_max} staff_active_est={staff_active_est} "
            f"queue_avg_seconds={queue_avg_seconds} frames_with_detections={frames_with_detections} "
            f"avg_detections_per_frame={avg_detections:.2f} "
            f"frames_processed_for_detection={frames_processed_for_detection} stride={stride} "
            f"lines_defined_count={lines_defined_count} line_crossings_count={line_crossings_str}"
        )
        print(message)
        self.logger.info(message)

    def _log_startup_info(self) -> None:
        zones_count = 0
        lines_count = 0
        roi_path = self.cfg.roi_path or ""
        if self._roi_override:
            zones_count = len(self._roi_override.get("zones") or {})
            lines_count = len(self._roi_override.get("lines") or {})
        elif self.cfg.source == "video":
            camera_id = self._get_video_camera_id()
            roi = self._load_roi_for_camera(camera_id)
            zones_count = len(roi.get("zones") or {})
            lines_count = len(roi.get("lines") or {})
            roi_path = self._roi_path_by_camera.get(camera_id, roi_path)
        elif not roi_path:
            roi_path = str(self._programdata_roi_path("<camera_id>"))
        model_path = _env_str("VISION_MODEL_PATH", "").strip() or "yolov8n.pt"
        self.logger.info(
            "[VISION] startup source=%s roi_path=%s zones_count=%s lines_count=%s model_path=%s",
            self.cfg.source,
            roi_path,
            zones_count,
            lines_count,
            model_path,
        )

    def _send_event(self, payload: dict):
        event_name = "vision.metrics.v1"
        bucket_start = payload["bucket"]["start"]
        camera_id = payload.get("camera_id") or ""
        roi_version = payload.get("roi_version") or 0
        receipt_id = _sha256(f"{event_name}|{self.store_id}|{camera_id}|{bucket_start}|{roi_version}")

        envelope = {
            "event_name": event_name,
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload["bucket"]["end"],
            "data": payload,
        }
        self._send_or_enqueue(envelope=envelope, context=event_name)

    def _send_crossing_event(
        self,
        *,
        cam: dict,
        line_name: str,
        line_meta: dict,
        direction: str,
        ts: float,
        track_id: int,
    ) -> None:
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        roi_version = (cam.get("roi") or {}).get("roi_version")
        track_hash = _sha256(f"{camera_id}|{track_id}")
        event_name = "vision.crossing.v1"
        receipt_id = _sha256(
            f"{event_name}|{self.store_id}|{camera_id}|{line_name}|{direction}|{int(ts * 1000)}|{track_hash}"
        )
        payload = {
            "event_type": event_name,
            "store_id": self.store_id,
            "camera_id": camera_id,
            "camera_role": self.cfg.video_role or cam.get("role") or self._resolve_role(cam) or "entrada",
            "zone_id": line_meta.get("zone_id") or cam.get("zone_id"),
            "roi_entity_id": line_meta.get("roi_entity_id") or line_name,
            "roi_version": roi_version,
            "metric_type": line_meta.get("metric_type") or "entry_exit",
            "ownership": line_meta.get("ownership") or "primary",
            "direction": direction,
            "count_value": 1,
            "confidence": 1.0,
            "track_id_hash": track_hash,
            "ts": _iso(ts),
        }
        envelope = {
            "event_name": event_name,
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload["ts"],
            "data": payload,
        }
        self._send_or_enqueue(envelope=envelope, context=f"{event_name}:{camera_id}:{direction}")

        retail_event_type = "person_enter" if direction == "entry" else "person_exit"
        self._send_retail_event(
            event_type=retail_event_type,
            value=1,
            ts=payload["ts"],
            camera_id=camera_id,
            zone_id=payload.get("zone_id"),
            roi_entity_id=payload.get("roi_entity_id"),
            metric_type="footfall",
            confidence=payload.get("confidence", 1.0),
        )

    def _send_queue_state_event(
        self,
        *,
        cam: dict,
        roi: Optional[dict],
        queue_length: int,
        staff_active_est: int,
        ts: float,
    ) -> None:
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        roi_version = (cam.get("roi") or {}).get("roi_version")
        context = self._select_metric_context(
            roi,
            entity_type="zone",
            metric_type="queue",
            fallback_zone_id=cam.get("zone_id"),
        )
        event_name = "vision.queue_state.v1"
        receipt_id = _sha256(
            f"{event_name}|{self.store_id}|{camera_id}|{context.get('roi_entity_id')}|{int(ts * 1000)}|{queue_length}|{staff_active_est}"
        )
        payload = {
            "event_type": event_name,
            "store_id": self.store_id,
            "camera_id": camera_id,
            "camera_role": self.cfg.video_role or cam.get("role") or self._resolve_role(cam) or "balcao",
            "zone_id": context.get("zone_id"),
            "roi_entity_id": context.get("roi_entity_id"),
            "roi_version": roi_version,
            "metric_type": context.get("metric_type") or "queue",
            "ownership": context.get("ownership") or "primary",
            "count_value": int(queue_length),
            "staff_active_est": int(staff_active_est),
            "confidence": 1.0,
            "ts": _iso(ts),
        }
        envelope = {
            "event_name": event_name,
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload["ts"],
            "data": payload,
        }
        self._send_or_enqueue(
            envelope=envelope,
            context=f"{event_name}:{camera_id}:q{queue_length}:s{staff_active_est}",
        )

        self._send_retail_event(
            event_type="queue_length",
            value=int(queue_length),
            ts=payload["ts"],
            camera_id=camera_id,
            zone_id=payload.get("zone_id"),
            roi_entity_id=payload.get("roi_entity_id"),
            metric_type="queue",
            confidence=payload.get("confidence", 1.0),
        )
        self._send_retail_event(
            event_type="staff_detected",
            value=int(staff_active_est),
            ts=payload["ts"],
            camera_id=camera_id,
            zone_id=payload.get("zone_id"),
            roi_entity_id=payload.get("roi_entity_id"),
            metric_type="staff_presence",
            confidence=payload.get("confidence", 1.0),
        )

    def _send_zone_occupancy_event(
        self,
        *,
        cam: dict,
        roi: Optional[dict],
        occupancy_count: int,
        dwell_seconds_est: int,
        ts: float,
    ) -> None:
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        roi_version = (cam.get("roi") or {}).get("roi_version")
        context = self._select_metric_context(
            roi,
            entity_type="zone",
            metric_type="occupancy",
            fallback_zone_id=cam.get("zone_id"),
        )
        event_name = "vision.zone_occupancy.v1"
        receipt_id = _sha256(
            f"{event_name}|{self.store_id}|{camera_id}|{context.get('roi_entity_id')}|{int(ts * 1000)}|{occupancy_count}|{dwell_seconds_est}"
        )
        payload = {
            "event_type": event_name,
            "store_id": self.store_id,
            "camera_id": camera_id,
            "camera_role": self.cfg.video_role or cam.get("role") or self._resolve_role(cam) or "salao",
            "zone_id": context.get("zone_id"),
            "roi_entity_id": context.get("roi_entity_id"),
            "roi_version": roi_version,
            "metric_type": context.get("metric_type") or "occupancy",
            "ownership": context.get("ownership") or "primary",
            "count_value": int(occupancy_count),
            "duration_seconds": int(dwell_seconds_est),
            "confidence": 1.0,
            "ts": _iso(ts),
        }
        envelope = {
            "event_name": event_name,
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload["ts"],
            "data": payload,
        }
        self._send_or_enqueue(
            envelope=envelope,
            context=f"{event_name}:{camera_id}:occ{occupancy_count}",
        )

        self._send_retail_event(
            event_type="zone_dwell",
            value={
                "occupancy_count": int(occupancy_count),
                "dwell_seconds_est": int(dwell_seconds_est),
            },
            ts=payload["ts"],
            camera_id=camera_id,
            zone_id=payload.get("zone_id"),
            roi_entity_id=payload.get("roi_entity_id"),
            metric_type="zone_dwell",
            confidence=payload.get("confidence", 1.0),
        )

    def _track_checkout_cycle(
        self,
        *,
        state: dict,
        cam: dict,
        roi: Optional[dict],
        clients_at_pay: int,
        staff_active: int,
        ts: float,
    ) -> None:
        cycle = state.get("checkout_cycle") or {}
        in_cycle = bool(cycle.get("in_cycle"))
        interaction_start = cycle.get("interaction_start")
        last_checkout = float(cycle.get("last_checkout", -1e9))

        if clients_at_pay >= 1 and staff_active >= 0:
            if not in_cycle:
                cycle["in_cycle"] = True
                cycle["interaction_start"] = ts
            state["checkout_cycle"] = cycle
            return

        if not in_cycle:
            return

        duration_seconds = int(max(0, round(ts - float(interaction_start or ts))))
        cycle["in_cycle"] = False
        cycle["interaction_start"] = None
        state["checkout_cycle"] = cycle
        if duration_seconds < 2:
            return
        if (ts - last_checkout) < 4.0:
            return

        cycle["last_checkout"] = ts
        state["checkout_cycle"] = cycle
        state["agg"]["checkout_events"] = int(state["agg"].get("checkout_events") or 0) + 1
        self._send_checkout_proxy_event(
            cam=cam,
            roi=roi,
            duration_seconds=duration_seconds,
            interaction_count=1,
            ts=ts,
        )

    def _send_checkout_proxy_event(
        self,
        *,
        cam: dict,
        roi: Optional[dict],
        duration_seconds: int,
        interaction_count: int,
        ts: float,
    ) -> None:
        camera_id = str(cam.get("camera_id") or cam.get("id") or "")
        roi_version = (cam.get("roi") or {}).get("roi_version")
        context = self._select_metric_context(
            roi,
            entity_type="zone",
            metric_type="checkout_proxy",
            fallback_zone_id=cam.get("zone_id"),
        )
        event_name = "vision.checkout_proxy.v1"
        receipt_id = _sha256(
            f"{event_name}|{self.store_id}|{camera_id}|{context.get('roi_entity_id')}|{int(ts * 1000)}|{duration_seconds}|{interaction_count}"
        )
        payload = {
            "event_type": event_name,
            "store_id": self.store_id,
            "camera_id": camera_id,
            "camera_role": self.cfg.video_role or cam.get("role") or self._resolve_role(cam) or "balcao",
            "zone_id": context.get("zone_id"),
            "roi_entity_id": context.get("roi_entity_id"),
            "roi_version": roi_version,
            "metric_type": context.get("metric_type") or "checkout_proxy",
            "ownership": context.get("ownership") or "primary",
            "count_value": int(interaction_count),
            "duration_seconds": int(duration_seconds),
            "confidence": 1.0,
            "ts": _iso(ts),
        }
        envelope = {
            "event_name": event_name,
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": payload["ts"],
            "data": payload,
        }
        self._send_or_enqueue(
            envelope=envelope,
            context=f"{event_name}:{camera_id}:dur{duration_seconds}",
        )

        self._send_retail_event(
            event_type="sale_completed",
            value=int(interaction_count),
            ts=payload["ts"],
            camera_id=camera_id,
            zone_id=payload.get("zone_id"),
            roi_entity_id=payload.get("roi_entity_id"),
            metric_type="sale_proxy",
            confidence=payload.get("confidence", 1.0),
        )

    def _send_retail_event(
        self,
        *,
        event_type: str,
        value: Any,
        ts: str,
        camera_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        roi_entity_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        confidence: float = 1.0,
    ) -> None:
        if not self.cfg.retail_event_v1_enabled:
            return
        data = {
            "store_id": self.store_id,
            "ts": ts,
            "event_type": event_type,
            "value": value,
            "source": "edge",
            "confidence": confidence,
            "camera_id": camera_id,
            "zone_id": zone_id,
            "roi_entity_id": roi_entity_id,
            "metric_type": metric_type,
        }
        receipt_id = compute_idempotency_key(
            event_name="retail.event.v1",
            data=data,
            ts=ts,
            bucket_minutes=5,
        )
        envelope = {
            "event_name": "retail.event.v1",
            "source": "edge",
            "receipt_id": receipt_id,
            "idempotency_key": receipt_id,
            "ts": ts,
            "data": data,
        }
        self._send_or_enqueue(envelope=envelope, context=f"retail.event.v1:{event_type}")
