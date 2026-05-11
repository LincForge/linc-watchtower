from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from linc_watchtower.analyzers.base import FrameEvent


@dataclass
class MotionEvent(FrameEvent):
    @property
    def changed_pixels(self) -> int:
        return self.detail["changed_pixels"]

    @property
    def area_frac(self) -> float:
        return self.detail["area_frac"]


class MotionAnalyzer:
    """Frame-difference motion detector.

    threshold: per-pixel intensity delta required to count a pixel as 'changed'.
    min_area_frac: minimum fraction of pixels that must change before emitting an event.
    """

    def __init__(self, threshold: float = 25.0, min_area_frac: float = 0.005) -> None:
        self.threshold = threshold
        self.min_area_frac = min_area_frac
        self._prev_gray: np.ndarray | None = None

    def analyze(self, frame: np.ndarray) -> MotionEvent | None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        prev = self._prev_gray
        self._prev_gray = gray
        if prev is None:
            return None
        diff = cv2.absdiff(gray, prev)
        changed = int((diff > self.threshold).sum())
        total = diff.size
        frac = changed / total
        if frac < self.min_area_frac:
            return None
        return MotionEvent(
            kind="motion",
            detail={"changed_pixels": changed, "area_frac": frac},
        )
