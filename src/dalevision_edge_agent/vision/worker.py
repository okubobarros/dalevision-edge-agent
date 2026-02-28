from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from .geometry import line_side, point_in_polygon


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


@dataclass
class VisionConfig:
    enabled: bool = False
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

    def stop(self):
        self._stop.set()

    def run_forever(self):
        if not self.cfg.enabled:
            self.logger.info("[VISION] disabled (VISION_ENABLED=0)")
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
        }

    def _fresh_agg(self) -> dict:
        return {
            "frames": 0,
            "fila_sum": 0,
            "fila_max": 0,
            "consumo_sum": 0,
            "consumo_max": 0,
            "entries": 0,
            "exits": 0,
            "checkout_events": 0,
            "staff_active_est": 0,
        }

    def _fetch_cameras(self) -> List[dict]:
        url = f"{self.cloud_base_url}/api/v1/stores/{self.store_id}/cameras/"
        headers = {"X-EDGE-TOKEN": self.edge_token}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code >= 300:
                if resp.status_code == 403:
                    self.logger.warning(
                        "[VISION] cameras list 403: verifique STORE_ID e EDGE_TOKEN (ou gere novo token no wizard)."
                    )
                self.logger.warning("[VISION] cameras list failed %s %s", resp.status_code, resp.text[:200])
                return []
            return resp.json() or []
        except Exception as exc:
            self.logger.warning("[VISION] cameras list exception: %s", exc)
            return []

    def _resolve_role(self, cam: dict) -> Optional[str]:
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
        rtsp_url = cam.get("rtsp_url")
        if not rtsp_url:
            return None
        try:
            import cv2
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                return None
            ok, frame = cap.read()
            cap.release()
            if not ok:
                return None
            return frame
        except Exception:
            return None

    def _process_frame(self, state: dict, cam: dict, frame, ts: float) -> Optional[dict]:
        role = state["role"]
        roi = self._extract_roi(cam, frame)
        if not roi:
            return None

        zones = roi["zones"]
        lines = roi["lines"]

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
        if results and results.get("boxes"):
            for item in results["boxes"]:
                x1, y1, x2, y2, cls = item
                is_person = cls == 0
                is_phone = cls == self.cfg.phone_class_id
                if not is_person and not is_phone:
                    continue
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
        agg["frames"] += 1
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
        headers = {"X-EDGE-TOKEN": self.edge_token}
        try:
            resp = requests.post(url, json=envelope, headers=headers, timeout=10)
            self.logger.info("[VISION] alert sent status=%s type=%s", resp.status_code, payload.get("event_type"))
        except Exception as exc:
            self.logger.warning("[VISION] alert send failed: %s", exc)

    def _yolo_track(self, state: dict, frame) -> Optional[dict]:
        try:
            from ultralytics import YOLO
            if state.get("model") is None:
                state["model"] = YOLO(_env_str("VISION_MODEL_PATH", "yolov8n.pt"))
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
        headers = {"X-EDGE-TOKEN": self.edge_token}
        try:
            resp = requests.post(url, json=envelope, headers=headers, timeout=10)
            self.logger.info("[VISION] event sent status=%s receipt=%s", resp.status_code, receipt_id[:10])
        except Exception as exc:
            self.logger.warning("[VISION] event send failed: %s", exc)
