from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..cameras import build_auth_headers
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


def _safe_json_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _env_str(name: str, default: str) -> str:
    import os
    return os.getenv(name, default)


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
                self.tick_once()
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
            "line_crossings_count": None,
            "fila_sum": 0,
            "fila_max": 0,
            "consumo_sum": 0,
            "consumo_max": 0,
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
                self.logger.warning("[VISION] %s item=%s skipped (missing id/rtsp_url)", source, idx)
                continue
            cameras.append(normalized)
        return cameras, None

    def _normalize_camera(self, cam: Any) -> Optional[dict]:
        if not isinstance(cam, dict):
            return None
        camera_id = str(cam.get("camera_id") or cam.get("id") or "").strip()
        rtsp_url = str(cam.get("rtsp_url") or "").strip()
        if not camera_id or not rtsp_url:
            return None
        return {
            **cam,
            "id": camera_id,
            "camera_id": camera_id,
            "rtsp_url": rtsp_url,
            "name": str(cam.get("name") or "").strip(),
            "external_id": str(cam.get("external_id") or cam.get("name") or "").strip(),
        }

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
            cam["roi_local"] = self._load_roi_for_camera(camera_id)
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

        cameras_json_raw = _env_str("CAMERAS_JSON", "")
        cameras_from_env, env_error = self._parse_cameras_json(cameras_json_raw, source="CAMERAS_JSON")
        if env_error:
            self.logger.warning("[VISION] %s", env_error)
        if cameras_from_env:
            cameras = self._apply_roi_to_cameras(cameras_from_env)
            self._save_cameras_cache(cameras, source="CAMERAS_JSON")
            self.logger.info("[VISION] cameras source=CAMERAS_JSON loaded=%s", len(cameras))
            return cameras

        camera_sync_enabled = self._parse_bool_env("CAMERA_SYNC_ENABLED", True)
        if camera_sync_enabled:
            edge_cameras, edge_source = self._fetch_cameras_from_edge()
            if edge_cameras:
                cameras = self._apply_roi_to_cameras(edge_cameras)
                self._save_cameras_cache(cameras, source=edge_source or "edge")
                self.logger.info("[VISION] cameras source=%s loaded=%s", edge_source or "edge", len(cameras))
                return cameras
            self.logger.warning("[VISION] cameras edge sync unavailable; trying cache")
        else:
            self.logger.info("[VISION] cameras sync disabled (CAMERA_SYNC_ENABLED=0); using cache/env only")

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
        name = str(cam.get("name") or "").lower()
        ext = str(cam.get("external_id") or "").lower()
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
        started = time.perf_counter()
        try:
            import cv2
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                self.logger.info("[VISION] rtsp attempt camera_id=%s ok=0 elapsed_ms=%s reason=open_failed", camera_id, elapsed_ms)
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

    def _process_frame(self, state: dict, cam: dict, frame, ts: float) -> Optional[dict]:
        role = state["role"]
        agg = state["agg"]
        agg["frames"] += 1

        stride = max(1, int(self.cfg.frame_stride))
        if agg["frames"] % stride != 1:
            return None

        agg["frames_processed_for_detection"] += 1
        roi = self._extract_roi(cam, frame)
        if roi is None:
            return None

        zones = roi["zones"]
        lines = roi["lines"]
        state["roi_lines_count"] = len(lines)

        # MVP usa 1 frame por tick (RTSP ou snapshot).
        # Evoluir para tracking RTSP low-FPS para fluxo/checkout completo.
        import cv2
        h, w = frame.shape[:2]
        results = self._yolo_track(state, frame)
        fila_count = 0
        consumo_count = 0
        clients_at_pay = 0
        staff_at_cashier = 0

        phone_in_staff_zone = False
        people_detections = 0
        if results and results.get("boxes"):
            for item in results["boxes"]:
                x1, y1, x2, y2, cls = item
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
                elif role == "entrada":
                    # Snapshot-only cannot infer flow accurately.
                    pass

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
        if role == "salao":
            agg["consumo_sum"] += consumo_count
            agg["consumo_max"] = max(agg["consumo_max"], consumo_count)

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
            "ts": payload.get("occurred_at"),
            "data": payload,
        }
        url = f"{self.cloud_base_url}/api/edge/events/"
        headers = build_auth_headers(self.edge_token)
        try:
            resp = requests.post(url, json=envelope, headers=headers, timeout=10)
            self.logger.info("[VISION] alert sent status=%s type=%s", resp.status_code, payload.get("event_type"))
        except Exception as exc:
            self.logger.warning("[VISION] alert send failed: %s", exc)

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
            items = []
            for (x1, y1, x2, y2), cls in zip(boxes, clss):
                items.append([x1, y1, x2, y2, int(cls)])
            return {"boxes": items}
        except Exception as exc:
            self.logger.warning("[VISION] yolo failed: %s", exc)
            return None

    def _extract_roi(self, cam: dict, frame) -> Optional[dict]:
        if cam.get("roi_local"):
            roi_local = cam.get("roi_local") or {}
            zones_raw = roi_local.get("zones") or {}
            lines_raw = roi_local.get("lines") or {}
            zones: Dict[str, List[List[int]]] = {}
            for name, pts in zones_raw.items():
                if not name or not pts:
                    continue
                zones[name] = [[int(p[0]), int(p[1])] for p in pts]
            lines: Dict[str, List[List[int]]] = {}
            for name, pts in lines_raw.items():
                if not name or not pts or len(pts) != 2:
                    continue
                lines[name] = [[int(pts[0][0]), int(pts[0][1])], [int(pts[1][0]), int(pts[1][1])]]
            return {"zones": zones, "lines": lines}
        config_json = cam.get("roi") or {}
        if not isinstance(config_json, dict):
            return None
        zones_raw = config_json.get("zones") or []
        lines_raw = config_json.get("lines") or []

        h, w = frame.shape[:2]
        zones: Dict[str, List[List[int]]] = {}
        for z in zones_raw:
            name = z.get("name")
            pts = z.get("points") or []
            if not name or not pts:
                continue
            px = []
            for p in pts:
                px.append([int(p["x"] * w), int(p["y"] * h)])
            zones[name] = px

        lines: Dict[str, List[List[int]]] = {}
        for ln in lines_raw:
            name = ln.get("name")
            pts = ln.get("points") or []
            if not name or len(pts) != 2:
                continue
            p1 = [int(pts[0]["x"] * w), int(pts[0]["y"] * h)]
            p2 = [int(pts[1]["x"] * w), int(pts[1]["y"] * h)]
            lines[name] = [p1, p2]

        if not zones and not lines:
            return None
        return {"zones": zones, "lines": lines}

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

    def _build_payload(self, cam: dict, state: dict, last_metrics: dict, bucket_start: int, bucket_end: int) -> dict:
        agg = state["agg"]
        frames = max(agg["frames"], 1)
        payload = {
            "store_id": self.store_id,
            "camera_id": str(cam.get("camera_id") or cam.get("id") or ""),
            "roi_version": (cam.get("roi") or {}).get("roi_version"),
            "bucket": {
                "seconds": self.cfg.bucket_seconds,
                "start": _iso(bucket_start),
                "end": _iso(bucket_end),
            },
            "traffic": {
                "footfall": agg["entries"],
                "engaged": 0,
                "dwell_seconds_avg": 0,
            },
            "conversion": {
                "queue_avg_seconds": int(agg["fila_sum"] / frames) if frames else 0,
                "staff_active_est": int(agg["staff_active_est"]),
            },
            "debug": {
                "frame_source": "rtsp_or_snapshot",
                "snapshot_url_present": bool(cam.get("last_snapshot_url")),
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
            "ts": payload["bucket"]["end"],
            "data": payload,
        }
        url = f"{self.cloud_base_url}/api/edge/events/"
        headers = build_auth_headers(self.edge_token)
        try:
            resp = requests.post(url, json=envelope, headers=headers, timeout=10)
            self.logger.info("[VISION] event sent status=%s receipt=%s", resp.status_code, receipt_id[:10])
        except Exception as exc:
            self.logger.warning("[VISION] event send failed: %s", exc)
