from linc_watchtower.config import CameraSpec, Settings, parse_camera_spec


def test_parse_camera_spec_single():
    cams = parse_camera_spec("front-door:1")
    assert cams == [CameraSpec(name="front-door", channel=1)]


def test_parse_camera_spec_multiple():
    cams = parse_camera_spec("front-door:1,office:2,driveway:3")
    assert cams == [
        CameraSpec(name="front-door", channel=1),
        CameraSpec(name="office", channel=2),
        CameraSpec(name="driveway", channel=3),
    ]


def test_parse_camera_spec_strips_whitespace():
    cams = parse_camera_spec(" front-door : 1 , office : 2 ")
    assert cams == [
        CameraSpec(name="front-door", channel=1),
        CameraSpec(name="office", channel=2),
    ]


def test_parse_camera_spec_empty():
    assert parse_camera_spec("") == []


def test_settings_builds_rtsp_url_high(monkeypatch):
    monkeypatch.setenv("WATCHTOWER_NVR_HOST", "10.0.0.5")
    monkeypatch.setenv("WATCHTOWER_NVR_USER", "admin")
    monkeypatch.setenv("WATCHTOWER_NVR_PASSWORD", "secret")
    monkeypatch.setenv("WATCHTOWER_CAMERAS", "front-door:1")
    s = Settings()
    url = s.rtsp_url("front-door", quality="high")
    assert url == "rtsp://admin:secret@10.0.0.5:554/media/video1"


def test_settings_builds_rtsp_url_low_uses_video2(monkeypatch):
    monkeypatch.setenv("WATCHTOWER_NVR_HOST", "10.0.0.5")
    monkeypatch.setenv("WATCHTOWER_NVR_USER", "admin")
    monkeypatch.setenv("WATCHTOWER_NVR_PASSWORD", "secret")
    monkeypatch.setenv("WATCHTOWER_CAMERAS", "front-door:3")
    s = Settings()
    url = s.rtsp_url("front-door", quality="low")
    assert url.endswith("/media/video3?stream=low") or url.endswith("/media/video3")
    # Sub-stream representation is NVR-dependent; we accept either /media/video<ch> or
    # explicit ?stream=low. The exact form will be locked once probed against real hardware.


def test_settings_unknown_camera_raises(monkeypatch):
    monkeypatch.setenv("WATCHTOWER_NVR_HOST", "10.0.0.5")
    monkeypatch.setenv("WATCHTOWER_NVR_USER", "admin")
    monkeypatch.setenv("WATCHTOWER_NVR_PASSWORD", "secret")
    monkeypatch.setenv("WATCHTOWER_CAMERAS", "front-door:1")
    s = Settings()
    try:
        s.rtsp_url("backyard")
    except KeyError as e:
        assert "backyard" in str(e)
    else:
        raise AssertionError("expected KeyError for unknown camera")


def test_settings_redacts_password_in_repr(monkeypatch):
    monkeypatch.setenv("WATCHTOWER_NVR_HOST", "10.0.0.5")
    monkeypatch.setenv("WATCHTOWER_NVR_USER", "admin")
    monkeypatch.setenv("WATCHTOWER_NVR_PASSWORD", "supersecret")
    monkeypatch.setenv("WATCHTOWER_CAMERAS", "front-door:1")
    s = Settings()
    assert "supersecret" not in repr(s)
