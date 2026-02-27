from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from .config import load_config
from .geometry import bucket_index, line_side, point_in_polygon


CONF = 0.35
IOU = 0.45
FRAME_SKIP = 2
TARGET_WIDTH = 960

LINE_COOLDOWN_SECONDS = 4.0
AGG_BUCKET_SECONDS = 60

CHECKOUT_DWELL_SECONDS = 2.0
CHECKOUT_GLOBAL_FAILSAFE_SECONDS = 4.0

EXCLUDE_PAY_FROM_QUEUE = True


def _lazy_import_yolo():
    from ultralytics import YOLO
    return YOLO


def _lazy_import_cv2():
    import cv2
    return cv2


def run_video(
    *,
    video_path: str,
    config_path: str,
    role: str,
    model_path: str = "yolov8n.pt",
) -> Dict[str, Any]:
    YOLO = _lazy_import_yolo()
    cv2 = _lazy_import_cv2()

    zones, lines = load_config(config_path)
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps_in = cap.get(cv2.CAP_PROP_FPS) or 25
    w_in = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h_in = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = TARGET_WIDTH / w_in
    w = int(w_in * scale)
    h = int(h_in * scale)
    fps_out = fps_in / FRAME_SKIP

    zones_scaled = {
        zn: [[int(p[0] * scale), int(p[1] * scale)] for p in pts]
        for zn, pts in zones.items()
    }

    lines_scaled: Dict[str, Tuple[List[int], List[int]]] = {}
    for ln, pts in lines.items():
        p1 = [int(pts[0][0] * scale), int(pts[0][1] * scale)]
        p2 = [int(pts[1][0] * scale), int(pts[1][1] * scale)]
        lines_scaled[ln] = (p1, p2)

    track_line_side_state = defaultdict(dict)
    track_line_last_event = defaultdict(dict)

    in_checkout_cycle = False
    interaction_start_t = None
    last_checkout_t = -1e9
    checkout_events_total = 0

    entries = 0
    exits = 0
    fila_peak = 0
    consumo_peak = 0

    agg = defaultdict(lambda: {
        "fila_sum": 0, "fila_n": 0, "fila_max": 0,
        "consumo_sum": 0, "consumo_n": 0, "consumo_max": 0,
        "entries": 0, "exits": 0,
        "checkout_events": 0
    })

    processed = 0
    frame_idx = 0
    debug_last_counts = {"clients_at_pay": None, "staff_at_cashier": None}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % FRAME_SKIP != 0:
            continue

        frame = cv2.resize(frame, (w, h))
        processed += 1
        t_s = processed / fps_out
        b = bucket_index(t_s, AGG_BUCKET_SECONDS)

        results = model.track(
            frame, persist=True, verbose=False, conf=CONF, iou=IOU
        )[0]

        fila_count = 0
        consumo_count = 0
        clients_at_pay = 0
        staff_at_cashier = 0

        if results.boxes is not None and results.boxes.id is not None:
            ids = results.boxes.id.cpu().numpy().astype(int)
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            clss = results.boxes.cls.cpu().numpy().astype(int)

            for track_id, box, cls in zip(ids, boxes, clss):
                if cls != 0:
                    continue

                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                foot_y = int(y2)
                center_y = int((y1 + y2) / 2)

                if role == "balcao":
                    in_pay = False
                    in_fila = False

                    if "ponto_pagamento" in zones_scaled:
                        in_pay = point_in_polygon(cx, center_y, zones_scaled["ponto_pagamento"])
                        if in_pay:
                            clients_at_pay += 1

                    if "zona_funcionario_caixa" in zones_scaled:
                        if point_in_polygon(cx, center_y, zones_scaled["zona_funcionario_caixa"]):
                            staff_at_cashier += 1

                    if "area_atendimento_fila" in zones_scaled:
                        in_fila = point_in_polygon(cx, foot_y, zones_scaled["area_atendimento_fila"])
                        if in_fila:
                            if EXCLUDE_PAY_FROM_QUEUE and in_pay:
                                pass
                            else:
                                fila_count += 1

                elif role == "salao":
                    if "area_consumo" in zones_scaled and point_in_polygon(cx, foot_y, zones_scaled["area_consumo"]):
                        consumo_count += 1

                elif role == "entrada":
                    for ln, (p1, p2) in lines_scaled.items():
                        side = line_side(p1, p2, (cx, foot_y))
                        prev = track_line_side_state[track_id].get(ln)

                        if prev is not None:
                            crossed_entry = (prev < 0 and side > 0)
                            crossed_exit = (prev > 0 and side < 0)

                            if crossed_entry:
                                key = ("entry", ln)
                                last_t = track_line_last_event[track_id].get(key, -1e9)
                                if (t_s - last_t) >= LINE_COOLDOWN_SECONDS:
                                    entries += 1
                                    agg[b]["entries"] += 1
                                    track_line_last_event[track_id][key] = t_s

                            elif crossed_exit:
                                key = ("exit", ln)
                                last_t = track_line_last_event[track_id].get(key, -1e9)
                                if (t_s - last_t) >= LINE_COOLDOWN_SECONDS:
                                    exits += 1
                                    agg[b]["exits"] += 1
                                    track_line_last_event[track_id][key] = t_s

                        track_line_side_state[track_id][ln] = side

        if role == "balcao":
            debug_last_counts["clients_at_pay"] = clients_at_pay
            debug_last_counts["staff_at_cashier"] = staff_at_cashier

            interaction_now = (clients_at_pay >= 1) and (staff_at_cashier >= 1)
            if CHECKOUT_GLOBAL_FAILSAFE_SECONDS > 0 and (t_s - last_checkout_t) < CHECKOUT_GLOBAL_FAILSAFE_SECONDS:
                interaction_start_t = None
            else:
                if not in_checkout_cycle:
                    if interaction_now:
                        if interaction_start_t is None:
                            interaction_start_t = t_s
                        else:
                            if (t_s - interaction_start_t) >= CHECKOUT_DWELL_SECONDS:
                                checkout_events_total += 1
                                agg[b]["checkout_events"] += 1
                                in_checkout_cycle = True
                                last_checkout_t = t_s
                                interaction_start_t = None
                    else:
                        interaction_start_t = None
                else:
                    if not interaction_now:
                        in_checkout_cycle = False
                        interaction_start_t = None

        fila_peak = max(fila_peak, fila_count)
        consumo_peak = max(consumo_peak, consumo_count)

        if role == "balcao":
            agg[b]["fila_sum"] += fila_count
            agg[b]["fila_n"] += 1
            agg[b]["fila_max"] = max(agg[b]["fila_max"], fila_count)
        elif role == "salao":
            agg[b]["consumo_sum"] += consumo_count
            agg[b]["consumo_n"] += 1
            agg[b]["consumo_max"] = max(agg[b]["consumo_max"], consumo_count)

    cap.release()

    series = []
    for b in sorted(agg.keys()):
        row = {"bucket_minute": b, "bucket_seconds": AGG_BUCKET_SECONDS}
        if role == "balcao":
            row["fila_avg"] = round(agg[b]["fila_sum"] / agg[b]["fila_n"], 2) if agg[b]["fila_n"] else 0
            row["fila_max"] = agg[b]["fila_max"]
            row["checkout_events"] = agg[b]["checkout_events"]
        elif role == "salao":
            row["consumo_avg"] = round(agg[b]["consumo_sum"] / agg[b]["consumo_n"], 2) if agg[b]["consumo_n"] else 0
            row["consumo_max"] = agg[b]["consumo_max"]
        elif role == "entrada":
            row["entries"] = agg[b]["entries"]
            row["exits"] = agg[b]["exits"]
        series.append(row)

    return {
        "role": role,
        "video": video_path,
        "config": config_path,
        "entries": entries,
        "exits": exits,
        "fila_peak": fila_peak,
        "consumo_peak": consumo_peak,
        "checkout_events_total": checkout_events_total if role == "balcao" else 0,
        "series": series,
        "debug_last_counts": debug_last_counts if role == "balcao" else None,
    }


def write_report(path: str, report: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

