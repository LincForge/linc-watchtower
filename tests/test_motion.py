import numpy as np

from linc_watchtower.analyzers.motion import MotionAnalyzer, MotionEvent


def _solid(shape: tuple[int, int, int], value: int) -> np.ndarray:
    return np.full(shape, value, dtype=np.uint8)


def test_motion_analyzer_first_frame_no_event():
    a = MotionAnalyzer(threshold=20.0, min_area_frac=0.001)
    frame = _solid((120, 160, 3), 50)
    assert a.analyze(frame) is None  # no prior frame to diff against


def test_motion_analyzer_identical_frames_no_event():
    a = MotionAnalyzer(threshold=20.0, min_area_frac=0.001)
    frame = _solid((120, 160, 3), 50)
    a.analyze(frame)
    assert a.analyze(frame) is None


def test_motion_analyzer_huge_change_emits_event():
    a = MotionAnalyzer(threshold=20.0, min_area_frac=0.001)
    a.analyze(_solid((120, 160, 3), 50))
    bright = _solid((120, 160, 3), 200)
    event = a.analyze(bright)
    assert isinstance(event, MotionEvent)
    assert event.area_frac > 0.5
    assert event.changed_pixels > 0


def test_motion_analyzer_tiny_change_below_min_area_no_event():
    a = MotionAnalyzer(threshold=20.0, min_area_frac=0.5)
    a.analyze(_solid((120, 160, 3), 50))
    nearly_same = _solid((120, 160, 3), 50)
    nearly_same[0, 0] = 250  # one bright pixel
    assert a.analyze(nearly_same) is None


def test_motion_analyzer_threshold_filters_small_intensity_diffs():
    a = MotionAnalyzer(threshold=50.0, min_area_frac=0.001)
    a.analyze(_solid((120, 160, 3), 100))
    slightly_brighter = _solid((120, 160, 3), 110)  # only +10, below threshold 50
    assert a.analyze(slightly_brighter) is None
