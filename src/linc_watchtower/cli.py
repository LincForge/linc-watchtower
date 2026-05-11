from __future__ import annotations

import sys
import time

import click
import structlog

from linc_watchtower.analyzers.motion import MotionAnalyzer
from linc_watchtower.config import Settings
from linc_watchtower.rtsp import RtspStreamError, _redact, iter_frames, open_stream

log = structlog.get_logger(__name__)


@click.group()
def main() -> None:
    """linc-watchtower — AvertX/OpenEye NVR automation."""


@main.command()
def cameras() -> None:
    """List configured cameras and the RTSP URL each will use."""
    s = Settings()
    if not s.camera_specs:
        click.echo("no cameras configured. Set WATCHTOWER_CAMERAS in .env (see .env.example).")
        return
    for cam in s.camera_specs:
        url = s.rtsp_url(cam.name)
        click.echo(f"{cam.name:20} ch={cam.channel}  {_redact(url)}")


@main.command()
@click.argument("camera")
@click.option("--quality", type=click.Choice(["high", "low"]), default=None)
@click.option("--frames", type=int, default=5, help="frames to capture for the probe")
def probe(camera: str, quality: str | None, frames: int) -> None:
    """Connect to a camera, capture a few frames, print stats. No display window."""
    s = Settings()
    url = s.rtsp_url(camera, quality=quality)
    click.echo(f"probing {camera} via {_redact(url)}")
    captured = 0
    t0 = time.time()
    try:
        for frame in iter_frames(url, max_frames=frames):
            captured += 1
            click.echo(f"  frame {captured}: shape={frame.shape} dtype={frame.dtype}")
    except RtspStreamError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    dt = time.time() - t0
    click.echo(f"captured {captured}/{frames} frames in {dt:.2f}s")


@main.command()
@click.argument("camera")
@click.option("--quality", type=click.Choice(["high", "low"]), default=None)
def stream(camera: str, quality: str | None) -> None:
    """Open a live preview window for a camera. Press 'q' to quit."""
    import cv2

    s = Settings()
    url = s.rtsp_url(camera, quality=quality)
    click.echo(f"streaming {camera} ({_redact(url)}). Press 'q' in the window to quit.")
    with open_stream(url) as cap:
        while True:
            ok, frame = cap.read()
            if not ok:
                click.echo("stream ended.")
                break
            cv2.imshow(f"watchtower :: {camera}", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cv2.destroyAllWindows()


@main.command()
@click.argument("camera")
@click.option("--quality", type=click.Choice(["high", "low"]), default="low")
@click.option("--threshold", type=float, default=25.0)
@click.option("--min-area-frac", type=float, default=0.01)
@click.option("--max-events", type=int, default=0, help="stop after N events; 0 = forever")
def watch(
    camera: str,
    quality: str | None,
    threshold: float,
    min_area_frac: float,
    max_events: int,
) -> None:
    """Stream + run the motion analyzer; emit JSON events to stdout."""
    import json

    s = Settings()
    url = s.rtsp_url(camera, quality=quality)
    analyzer = MotionAnalyzer(threshold=threshold, min_area_frac=min_area_frac)
    click.echo(f"watching {camera} ({_redact(url)}) thr={threshold} min_area={min_area_frac}")
    seen = 0
    for frame in iter_frames(url):
        ev = analyzer.analyze(frame)
        if ev is None:
            continue
        seen += 1
        click.echo(
            json.dumps(
                {
                    "ts": time.time(),
                    "camera": camera,
                    "kind": ev.kind,
                    "area_frac": round(ev.detail["area_frac"], 4),
                    "changed_pixels": ev.detail["changed_pixels"],
                }
            )
        )
        if max_events and seen >= max_events:
            break


if __name__ == "__main__":
    main()
