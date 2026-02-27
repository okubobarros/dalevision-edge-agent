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

        if results and results.get("boxes"):
            for item in results["boxes"]:
                x1, y1, x2, y2, cls = item
                if cls != 0:
                    continue
                cx = int((x1 + x2) / 2)
                foot_y = int(y2)
                center_y = int((y1 + y2) / 2)

                if role == "balcao":
                    in_pay = "ponto_pagamento" in zones and point_in_polygon(cx, center_y, zones["ponto_pagamento"])
                    if in_pay:
                        clients_at_pay += 1
                    if "zona_funcionario_caixa" in zones and point_in_polygon(cx, center_y, zones["zona_funcionario_caixa"]):
                        staff_at_cashier += 1
                    if "area_atendimento_fila" in zones and point_in_polygon(cx, foot_y, zones["area_atendimento_fila"]):
                        if not (in_pay and _env_str("EXCLUDE_PAY_FROM_QUEUE", "1") == "1"):
                            fila_count += 1
                elif role == "salao":
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

        return {
            "fila_count": fila_count,
            "consumo_count": consumo_count,
            "staff_active": staff_at_cashier,
        }

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
