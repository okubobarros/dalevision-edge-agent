import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Tuple

import cv2
import yaml
import numpy as np


@dataclass
class Frame:
    image: Any  # np.ndarray (BGR)
    ts: float


def _point_in_polygon(px: float, py: float, polygon: List[List[int]]) -> bool:
    """
    polygon: [[x,y], [x,y], ...]
    """
    if not polygon or len(polygon) < 3:
        return False
    contour = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(contour, (float(px), float(py)), False) >= 0


def _line_side(p1: Tuple[int, int], p2: Tuple[int, int], p: Tuple[int, int]) -> float:
    """
    Retorna o "lado" do ponto p em relação à linha p1->p2.
    Mesma ideia do runner v4.2 (entrada/saída).
    """
    return (p2[0] - p1[0]) * (p[1] - p1[1]) - (p2[1] - p1[1]) * (p[0] - p1[0])


class RtspCameraWorker(threading.Thread):
    def __init__(
        self,
        camera_id: str,
        name: str,
        rtsp_url: str,
        roi_config_path: str,
        target_width: int,
        fps_limit: int,
        frame_skip: int,
    ):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.name = name
        self.rtsp_url = rtsp_url
        self.target_width = target_width
        self.fps_limit = fps_limit
        self.frame_skip = frame_skip

        self._stop = False
        self._last_frame: Optional[Frame] = None
        self._ok = False
        self._last_err = None

        if not os.path.exists(roi_config_path):
            logging.warning(
                "[ROI] arquivo não encontrado: %s (camera %s). Rodando sem ROI.",
                roi_config_path,
                self.camera_id,
            )
            self.roi = {}
        else:
            with open(roi_config_path, "r", encoding="utf-8") as f:
                self.roi = yaml.safe_load(f) or {}

        # estado interno (checkout FSM, linhas etc.)
        self._roi_state: Dict[str, Any] = {
            # checkout FSM
            "in_checkout_cycle": False,
            "interaction_start_ts": None,
            "last_checkout_ts": -1e9,

            # entrada/saída (precisa track_id)
            "track_line_side_state": {},   # track_id -> {line_name: side}
            "track_line_last_event": {},   # track_id -> {(entry/exit,line_name): last_ts}

            # debug
            "debug_last_counts": {
                "clients_at_pay": 0,
                "staff_at_cashier": 0,
            }
        }

        # cache de zonas/linhas
        self._zones: Dict[str, List[List[int]]] = (self.roi.get("zones", {}) or {})
        self._lines_raw = (self.roi.get("lines", {}) or {})

        # normaliza linhas: {"linha_entrada_saida": [[x,y],[x,y]]} -> (p1,p2)
        self._lines: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {}
        for ln, pts in self._lines_raw.items():
            if isinstance(pts, list) and len(pts) == 2:
                p1 = (int(pts[0][0]), int(pts[0][1]))
                p2 = (int(pts[1][0]), int(pts[1][1]))
                self._lines[ln] = (p1, p2)

        # params (defaults iguais ao runner)
        params = self.roi.get("params", {}) or {}
        self._exclude_pay_from_queue: bool = bool(params.get("exclude_pay_from_queue", True))
        self._checkout_dwell_s: float = float(params.get("checkout_dwell_seconds", 2.0))
        self._checkout_failsafe_s: float = float(params.get("checkout_failsafe_seconds", 4.0))
        self._line_cooldown_s: float = float(params.get("line_cooldown_seconds", 4.0))

    def _is_rtsp(self) -> bool:
        return isinstance(self.rtsp_url, str) and self.rtsp_url.lower().startswith("rtsp://")

    def run(self):
        cap = None
        last_emit = 0.0
        skip = 0

        while not self._stop:
            try:
                # (re)open
                if cap is None or not cap.isOpened():
                    cap = cv2.VideoCapture(self.rtsp_url)
                    time.sleep(0.3)

                ok, frame = cap.read()

                # ========= EOF / RTSP fail handling =========
                if not ok or frame is None:
                    self._ok = False

                    # ✅ Se for arquivo (mp4) e acabou: volta pro começo e continua
                    if not self._is_rtsp():
                        try:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            time.sleep(0.05)
                            continue
                        except Exception as e:
                            self._last_err = f"video_loop_error: {e}"

                    # ✅ Se for RTSP (ou falha séria): libera e tenta reabrir
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = None
                    time.sleep(0.5)
                    continue

                self._ok = True

                # frame skip
                skip += 1
                if skip <= self.frame_skip:
                    continue
                skip = 0

                # resize
                h, w = frame.shape[:2]
                if w > self.target_width:
                    scale = self.target_width / float(w)
                    frame = cv2.resize(frame, (self.target_width, int(h * scale)))

                # fps limit
                now = time.time()
                if self.fps_limit > 0 and (now - last_emit) < (1.0 / self.fps_limit):
                    # pequena pausa pra não girar em loop apertado
                    time.sleep(0.001)
                    continue
                last_emit = now

                self._last_frame = Frame(image=frame, ts=now)

            except Exception as e:
                self._last_err = str(e)
                self._ok = False
                # tenta resetar a captura em caso de erro
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
                cap = None
                time.sleep(0.5)

        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass

    def stop(self):
        self._stop = True

    def try_get_frame(self) -> Optional[Frame]:
        f = self._last_frame
        self._last_frame = None
        return f

    def is_ok(self) -> bool:
        return bool(self._ok)

    def _infer_role(self) -> str:
        """
        Se o YAML tiver role, usa. Senão infere pela presença das ROIs.
        """
        role = self.roi.get("role")
        if role in ("balcao", "salao", "entrada"):
            return role

        z = self._zones
        if "ponto_pagamento" in z or "area_atendimento_fila" in z or "zona_funcionario_caixa" in z:
            return "balcao"
        if "area_consumo" in z:
            return "salao"
        if self._lines:
            return "entrada"
        return "unknown"

    def update_metrics(self, detections, ts: float):
        """
        Entrada:
          detections: lista de detecções (idealmente de pessoas).
            Aceita:
              - objetos com .xyxy e opcional .track_id/.id
              - dicts com keys: xyxy, track_id
        Saída v1 (estável):
          {
            "people_count": int,
            "queue_count": int,
            "pay_count": int,
            "staff_count": int,
            "consumo_count": int,
            "checkout_events": int,  # increment no frame (0/1)
            "entries": int,          # increment no frame (0/1/..)
            "exits": int             # increment no frame (0/1/..)
          }
        """
        role = self._infer_role()

        zones = self._zones
        lines = self._lines

        queue_count = 0
        pay_count = 0
        staff_count = 0
        consumo_count = 0

        # increments (por frame)
        checkout_events_inc = 0
        entries_inc = 0
        exits_inc = 0

        # para checkout FSM (somente balcão)
        clients_at_pay = 0
        staff_at_cashier = 0

        # ===== loop detections =====
        for det in (detections or []):
            # extrai xyxy
            if isinstance(det, dict):
                xyxy = det.get("xyxy")
                track_id = det.get("track_id")
            else:
                xyxy = getattr(det, "xyxy", None)
                track_id = getattr(det, "track_id", None)
                if track_id is None:
                    track_id = getattr(det, "id", None)

            if not xyxy or len(xyxy) != 4:
                continue

            x1, y1, x2, y2 = xyxy
            cx = (float(x1) + float(x2)) / 2.0
            foot_y = float(y2)                 # pé (chão)
            center_y = (float(y1) + float(y2)) / 2.0  # tronco/centro

            if role == "balcao":
                in_pay = False
                in_queue = False

                # pagamento: usa centro
                if "ponto_pagamento" in zones:
                    in_pay = _point_in_polygon(cx, center_y, zones["ponto_pagamento"])
                    if in_pay:
                        clients_at_pay += 1
                        pay_count += 1

                # funcionário: usa centro (tronco) para evitar oclusão do pé
                if "zona_funcionario_caixa" in zones:
                    if _point_in_polygon(cx, center_y, zones["zona_funcionario_caixa"]):
                        staff_at_cashier += 1
                        staff_count += 1

                # fila: usa pé, mas com regra pagamento > fila
                if "area_atendimento_fila" in zones:
                    in_queue = _point_in_polygon(cx, foot_y, zones["area_atendimento_fila"])
                    if in_queue:
                        if self._exclude_pay_from_queue and in_pay:
                            pass  # pagamento tem prioridade
                        else:
                            queue_count += 1

            elif role == "salao":
                if "area_consumo" in zones and _point_in_polygon(cx, foot_y, zones["area_consumo"]):
                    consumo_count += 1

            elif role == "entrada":
                # entrada/saída requer track_id para lado anterior
                if track_id is None or not lines:
                    continue

                tls = self._roi_state["track_line_side_state"]
                tll = self._roi_state["track_line_last_event"]

                if track_id not in tls:
                    tls[track_id] = {}
                if track_id not in tll:
                    tll[track_id] = {}

                for ln, (p1, p2) in lines.items():
                    side = _line_side(p1, p2, (int(cx), int(foot_y)))
                    prev = tls[track_id].get(ln)

                    if prev is not None:
                        crossed_entry = (prev < 0 and side > 0)
                        crossed_exit = (prev > 0 and side < 0)

                        if crossed_entry:
                            key = ("entry", ln)
                            last_t = tll[track_id].get(key, -1e9)
                            if (ts - last_t) >= self._line_cooldown_s:
                                entries_inc += 1
                                tll[track_id][key] = ts

                        elif crossed_exit:
                            key = ("exit", ln)
                            last_t = tll[track_id].get(key, -1e9)
                            if (ts - last_t) >= self._line_cooldown_s:
                                exits_inc += 1
                                tll[track_id][key] = ts

                    tls[track_id][ln] = side

        # ===== checkout FSM (balcão) =====
        if role == "balcao":
            self._roi_state["debug_last_counts"]["clients_at_pay"] = clients_at_pay
            self._roi_state["debug_last_counts"]["staff_at_cashier"] = staff_at_cashier

            interaction_now = (clients_at_pay >= 1) and (staff_at_cashier >= 1)

            in_cycle = bool(self._roi_state["in_checkout_cycle"])
            interaction_start = self._roi_state["interaction_start_ts"]
            last_checkout_ts = float(self._roi_state["last_checkout_ts"])

            # failsafe (airbag)
            if self._checkout_failsafe_s > 0 and (ts - last_checkout_ts) < self._checkout_failsafe_s:
                interaction_start = None
            else:
                if not in_cycle:
                    if interaction_now:
                        if interaction_start is None:
                            interaction_start = ts
                        else:
                            if (ts - interaction_start) >= self._checkout_dwell_s:
                                checkout_events_inc = 1
                                in_cycle = True
                                last_checkout_ts = ts
                                interaction_start = None
                    else:
                        interaction_start = None
                else:
                    # rearma quando a interação termina
                    if not interaction_now:
                        in_cycle = False
                        interaction_start = None

            self._roi_state["in_checkout_cycle"] = in_cycle
            self._roi_state["interaction_start_ts"] = interaction_start
            self._roi_state["last_checkout_ts"] = last_checkout_ts

        return {
            "people_count": len(detections or []),

            # balcão
            "queue_count": int(queue_count),
            "pay_count": int(pay_count),
            "staff_count": int(staff_count),
            "checkout_events": int(checkout_events_inc),

            # salão
            "consumo_count": int(consumo_count),

            # entrada
            "entries": int(entries_inc),
            "exits": int(exits_inc),

            # debug opcional
            "debug_clients_at_pay": int(self._roi_state["debug_last_counts"]["clients_at_pay"]),
            "debug_staff_at_cashier": int(self._roi_state["debug_last_counts"]["staff_at_cashier"]),
        }
