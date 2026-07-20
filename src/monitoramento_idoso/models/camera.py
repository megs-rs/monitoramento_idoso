from dataclasses import dataclass, field


@dataclass
class CameraInfo:
    ip: str
    port: int
    manufacturer: str = ""
    model: str = ""
    firmware_version: str = ""
    scopes: list[str] = field(default_factory=list)
    xaddrs: list[str] = field(default_factory=list)
    rtsp_urls: dict[str, str] = field(default_factory=dict)
