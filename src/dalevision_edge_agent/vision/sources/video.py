from __future__ import annotations

import os
import time
from typing import Generator, Optional, Tuple


class VideoFrameSource:
    def __init__(self, *, path: str, realtime: bool, loop: bool, logger) -> None:
        self.path = path
        self.realtime = realtime
        self.loop = loop
        self.logger = logger

    def frames(self) -> Generator[Tuple[object, float], None, None]:
        if not self.path:
            raise RuntimeError("VISION_VIDEO_PATH vazio.")
        if not os.path.exists(self.path):
            raise RuntimeError(f"Arquivo de video nao encontrado: {self.path}")

        import cv2

        cap = cv2.VideoCapture(self.path)
        if not cap.isOpened():
            raise RuntimeError(f"Nao foi possivel abrir o video: {self.path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0
        frame_index = 0
        start_ts = time.time()

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    if self.loop:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        frame_index = 0
                        start_ts = time.time()
                        continue
                    break
                ts = start_ts + (frame_index / fps)
                if self.realtime:
                    delay = ts - time.time()
                    if delay > 0:
                        time.sleep(delay)
                yield frame, ts
                frame_index += 1
        finally:
            cap.release()
