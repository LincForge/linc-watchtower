# linc-watchtower

AvertX/OpenEye NVR automation — pull live RTSP frames from your NVR and run pluggable analyzers (motion-diff, eventually computer-vision models).

Status: **prototype**, RTSP path only. Cloud (AvertX Connect / OWS) and local Apex REST trigger paths are stubbed for later.

## Quick start

```bash
cd ~/projects/linc-watchtower
uv sync --extra dev
cp .env.example .env  # then edit with your NVR address + creds
uv run pytest          # 13 tests, all green
```

### Configure cameras

Edit `.env`:

```
WATCHTOWER_NVR_HOST=192.168.1.50
WATCHTOWER_NVR_USER=admin
WATCHTOWER_NVR_PASSWORD=...
WATCHTOWER_CAMERAS=front-door:1,office:2,driveway:3
```

`WATCHTOWER_CAMERAS` is `name:channel` pairs. The channel maps to the NVR's RTSP URI as `/media/video<channel>` (OpenEye/AvertX native convention; see `reference_avertx_nvr_api.md` in LINC memory).

### CLI

```bash
uv run watchtower cameras                              # list configured cameras
uv run watchtower probe front-door --frames 5         # capture 5 frames, print stats
uv run watchtower stream front-door                    # live preview window (press q to quit)
uv run watchtower watch front-door --max-events 10     # stream + JSON motion events to stdout
```

## Roadmap

| Path | Status | Notes |
|------|--------|-------|
| RTSP frame ingest + motion analyzer | ✅ Working | This prototype. |
| Per-camera channel discovery via ONVIF | TODO | Replace manual `WATCHTOWER_CAMERAS` config. |
| Cloud OWS API client (`restapi.gp4f.com`) | TODO | Async MP4 export, Integration ID enumeration, event polling. Needs Access Key from AvertX Connect → Management → Integrations. |
| Local Apex Software Trigger reverse-engineer | TODO | Burp/Fiddler the local web UI to discover the trigger POST. Then external sensors can force-record clips with near-zero latency. |
| AI analyzer plugin (object detection, person/vehicle classification) | TODO | The `Analyzer` protocol in `analyzers/base.py` is the extension point. |
| linc-nerve adapter (treat the NVR as a "video device") | TODO | If this graduates from prototype to platform tool. |

## Architecture notes

- `config.py` — `Settings` reads `WATCHTOWER_*` env (or `.env`); builds RTSP URLs.
- `rtsp.py` — thin OpenCV wrapper. `iter_frames(url)` is the workhorse; `open_stream(url)` is a context manager with guaranteed release.
- `analyzers/base.py` — `Analyzer` protocol. Implementers return `FrameEvent | None` per frame.
- `analyzers/motion.py` — frame-difference detector. Threshold = per-pixel intensity delta; min_area_frac = fraction of pixels that must change to emit an event.
- `cli.py` — `cameras`/`probe`/`stream`/`watch` Click commands. `watch` emits JSON to stdout, easy to pipe into anything.

## Why this exists

LINC already has nerve (device comms) and crucible (quality scoring). The home-office NVR is the next "device" worth pulling into that fabric — for fun, for security drills, and as a testbed for the AI-on-video-feeds capability that will eventually serve customer products.
