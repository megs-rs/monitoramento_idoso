from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    id: int | None = None
    timestamp: datetime | None = None
    camera_ip: str = ""
    event_type: str = ""
    clip_path: str = ""
