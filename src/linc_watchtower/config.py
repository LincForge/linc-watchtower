from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class CameraSpec:
    name: str
    channel: int


def parse_camera_spec(raw: str) -> list[CameraSpec]:
    if not raw or not raw.strip():
        return []
    out: list[CameraSpec] = []
    for entry in raw.split(","):
        if not entry.strip():
            continue
        name, _, channel = entry.partition(":")
        out.append(CameraSpec(name=name.strip(), channel=int(channel.strip())))
    return out


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WATCHTOWER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nvr_host: str = Field(default="127.0.0.1")
    nvr_rtsp_port: int = Field(default=554)
    nvr_user: str = Field(default="admin")
    nvr_password: SecretStr = Field(default=SecretStr(""))
    default_stream: str = Field(default="low")
    cameras: str = Field(default="")

    @property
    def camera_specs(self) -> list[CameraSpec]:
        return parse_camera_spec(self.cameras)

    def find_camera(self, name: str) -> CameraSpec:
        for cam in self.camera_specs:
            if cam.name == name:
                return cam
        raise KeyError(f"camera '{name}' not in WATCHTOWER_CAMERAS")

    def rtsp_url(self, camera: str, *, quality: str | None = None) -> str:
        cam = self.find_camera(camera)
        q = (quality or self.default_stream).lower()
        # OpenEye/AvertX native convention: /media/video<channel>. The doc notes that
        # high vs. low sub-stream is NVR-dependent; OE's primary mapping is video1=high,
        # video2=low. When cameras are bridged through the NVR we treat `channel` as
        # the canonical video<N> integer and let `quality` toggle a hint suffix that
        # downstream NVRs may or may not honor — safe to ignore if not supported.
        path = f"/media/video{cam.channel}"
        if q == "low" and cam.channel == 1:
            # If user only configured channel 1 but asks for low, fall back to video2.
            path = "/media/video2"
        pwd = self.nvr_password.get_secret_value()
        return f"rtsp://{self.nvr_user}:{pwd}@{self.nvr_host}:{self.nvr_rtsp_port}{path}"
