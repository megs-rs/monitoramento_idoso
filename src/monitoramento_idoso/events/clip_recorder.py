from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)


class ClipRecorder:
    def __init__(self, duration_seconds: int = 30, fps: float = 15.0):
        self.duration_seconds = duration_seconds
        self.fps = fps
        self._buffer: deque[tuple[float, object]] = deque()
        self._max_frames = int(duration_seconds * fps)

    def add_frame(self, frame) -> None:
        timestamp = time.time()
        self._buffer.append((timestamp, frame))
        while len(self._buffer) > self._max_frames:
            self._buffer.popleft()

    def save(self, camera_ip: str, output_dir: Path | str = "clips") -> Path | None:
        if not self._buffer:
            logger.warning("No frames in buffer for %s", camera_ip)
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{camera_ip.replace('.', '_')}.mp4"
        output_path = output_dir / filename

        frames = list(self._buffer)
        if not frames:
            return None

        sample_frame = frames[0][1]
        h, w = sample_frame.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, self.fps, (w, h))

        for _, frame in frames:
            writer.write(frame)

        writer.release()
        logger.info("Clip saved: %s (%d frames)", output_path, len(frames))
        return output_path
