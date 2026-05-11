<!-- AUTO-GENERATED FROM LINC.md — DO NOT EDIT -->
<!-- LINC_CONTEXT_v1_hash:71717dd11b6d -->

# linc-watchtower

AvertX/OpenEye NVR automation. Live RTSP frame ingest + pluggable analyzers.

**Status:** prototype (RTSP path only).

## Project context

The AvertX ProConnect series is an OpenEye OEM. There are three programmatic surfaces:

1. **Direct RTSP** to the NVR — lowest latency, no cloud dependency. ← **this project, today.**
2. **Cloud OWS API** at `restapi.gp4f.com` — async MP4 export, JSON event push/pull. Needs a provisioned Access Key + Secret from AvertX Connect → Management → Integrations.
3. **Local Apex REST API** — undocumented; reverse-engineered via Burp/Fiddler. Useful for low-latency local triggers (e.g. an external sensor commands the NVR to bookmark / force-record).

The full deep-research source lives in LINC memory: `reference_avertx_nvr_api.md`.

## Layout

```
src/linc_watchtower/
  config.py        # pydantic-settings, env-driven RTSP URL builder
  rtsp.py          # cv2.VideoCapture wrapper, frame iterator, URL redaction
  analyzers/
    base.py        # Analyzer protocol + FrameEvent dataclass
    motion.py      # frame-diff motion detector
  cli.py           # click CLI: cameras / probe / stream / watch
tests/
  test_config.py
  test_motion.py
```

## Running locally

```bash
uv sync --extra dev
cp .env.example .env  # edit with NVR creds
uv run pytest          # 13 tests
uv run watchtower cameras
uv run watchtower probe <name> --frames 5
uv run watchtower watch <name> --max-events 10
```

## Operational Notes

- Cameras are PoE'd to the NVR's internal switch (per CEO's network setup). RTSP must therefore target the NVR's LAN address with a per-camera channel — not the camera IP, since the cameras aren't on the user's LAN.
- The `quality=low` flag in `Settings.rtsp_url` falls back to `/media/video2` only when the configured channel is 1. For multi-channel NVR setups, configure the actual sub-stream channel directly in `WATCHTOWER_CAMERAS`.
- `_redact()` in `rtsp.py` is used everywhere a URL is logged. Don't bypass it — RTSP URLs include credentials in the userinfo segment.
- No cloud API keys live in this repo. When the OWS path is added, keys will be sourced from `WATCHTOWER_OWS_ACCESS_KEY` / `WATCHTOWER_OWS_SECRET` env vars.

## Roadmap

See README.md.
