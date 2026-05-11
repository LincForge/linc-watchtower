from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import cv2
import numpy as np


class RtspStreamError(RuntimeError):
    pass


@contextmanager
def open_stream(url: str, *, timeout_sec: float = 10.0) -> Iterator[cv2.VideoCapture]:
    """Open an RTSP stream, yield the cv2.VideoCapture, guarantee release."""
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    # OpenCV honors OPENCV_FFMPEG_CAPTURE_OPTIONS for advanced config; default TCP transport
    # gives more reliable delivery over WiFi than UDP.
    if not cap.isOpened():
        cap.release()
        raise RtspStreamError(f"failed to open RTSP stream: {_redact(url)}")
    try:
        yield cap
    finally:
        cap.release()


def iter_frames(url: str, *, max_frames: int | None = None) -> Iterator[np.ndarray]:
    with open_stream(url) as cap:
        produced = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
            produced += 1
            if max_frames is not None and produced >= max_frames:
                break


def _redact(url: str) -> str:
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    _creds, host = rest.split("@", 1)
    return f"{scheme}://***:***@{host}"
