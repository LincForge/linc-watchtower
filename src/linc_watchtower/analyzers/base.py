from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class FrameEvent:
    kind: str
    detail: dict


class Analyzer(Protocol):
    def analyze(self, frame: np.ndarray) -> FrameEvent | None: ...
