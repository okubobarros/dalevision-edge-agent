from __future__ import annotations
import numpy as np
import time
import logging

class AdaptiveMotionGate:
    def __init__(self, logger: logging.Logger, calibration_seconds: int = 600):
        self.logger = logger
        self.calibration_seconds = calibration_seconds
        self.calibrated = False
        self.start_ts = time.time()
        self.deltas = []
        self.threshold = None
        self.last_gray = None

    def process(self, frame) -> bool:
        """
        Retorna True se houver movimento ou se ainda estiver calibrando.
        """
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.last_gray is None:
            self.last_gray = gray
            return True

        frame_delta = cv2.absdiff(self.last_gray, gray)
        self.last_gray = gray
        
        # Calculate score: sum of pixels > threshold (simple version)
        score = np.sum(frame_delta > 25)
        
        now = time.time()
        if not self.calibrated:
            self.deltas.append(score)
            if now - self.start_ts > self.calibration_seconds:
                self._calibrate()
            return True
        
        return score > self.threshold

    def _calibrate(self):
        if not self.deltas:
            self.threshold = 500 # Default fallback
        else:
            mean_val = np.mean(self.deltas)
            std_val = np.std(self.deltas)
            # Threshold = mean + 2*std (95% of noise absorbed)
            self.threshold = max(200, int(mean_val + 2 * std_val))
        
        self.calibrated = True
        self.logger.info(
            "[MOTION] Calibration done logic=adaptive threshold=%s samples=%s",
            self.threshold, len(self.deltas)
        )
        # Clear memory
        self.deltas = []
