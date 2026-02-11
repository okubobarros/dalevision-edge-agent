# edge-agent/src/vision/detector.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import numpy as np

try:
    from ultralytics import YOLO
except Exception as e:
    YOLO = None  # type: ignore


@dataclass
class Detection:
    cls_name: str
    conf: float
    xyxy: List[float]  # [x1,y1,x2,y2]


class PersonDetector:
    def __init__(
        self,
        weights_path: str,
        conf: float = 0.35,
        iou: float = 0.45,
        device: str = "cpu",
    ):
        if YOLO is None:
            raise RuntimeError("ultralytics não está instalado. pip install ultralytics")

        self.model = YOLO(weights_path)
        self.conf = conf
        self.iou = iou
        self.device = device

    def detect(self, frame_bgr: np.ndarray) -> List[Detection]:
        """
        Retorna apenas pessoas (class 0 no COCO geralmente).
        """
        results = self.model.predict(
            source=frame_bgr,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )

        dets: List[Detection] = []
        if not results:
            return dets

        r0 = results[0]
        if r0.boxes is None:
            return dets

        # boxes: xyxy, conf, cls
        xyxy = r0.boxes.xyxy.cpu().numpy()
        confs = r0.boxes.conf.cpu().numpy()
        clss = r0.boxes.cls.cpu().numpy().astype(int)

        # nomes (se existir)
        names = getattr(self.model, "names", None) or {}

        for box, cf, c in zip(xyxy, confs, clss):
            cls_name = names.get(c, str(c))
            if cls_name != "person" and c != 0:
                continue
            x1, y1, x2, y2 = [float(v) for v in box.tolist()]
            dets.append(Detection(cls_name="person", conf=float(cf), xyxy=[x1, y1, x2, y2]))

        return dets
