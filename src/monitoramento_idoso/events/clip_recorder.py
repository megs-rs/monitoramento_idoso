from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)


class ClipRecorder:
    def __init__(self, pre_seconds: int = 15, post_seconds: int = 15, fps: float = 15.0):
        self.pre_seconds = pre_seconds
        self.post_seconds = post_seconds
        self.fps = fps
        self._pre_buffer: deque[tuple[float, object]] = deque()
        self._post_buffer: list[tuple[float, object]] | None = None
        self._max_pre_frames = int(pre_seconds * fps)
        self._max_post_frames = int(post_seconds * fps)

    def add_frame(self, frame) -> bool:
        """Add frame to buffer. Returns True when post-event recording is complete."""
        timestamp = time.time()

        if self._post_buffer is not None:
            self._post_buffer.append((timestamp, frame))
            if len(self._post_buffer) >= self._max_post_frames:
                return True
            return False

        self._pre_buffer.append((timestamp, frame))
        while len(self._pre_buffer) > self._max_pre_frames:
            self._pre_buffer.popleft()
        return False

    def start_post_event(self) -> None:
        """Start recording post-event frames."""
        self._post_buffer = []
        logger.debug("Post-event recording started")

    def save(self, camera_ip: str, output_dir: Path | str = "clips") -> Path | None:
        """Save pre + post event clip."""
        pre = list(self._pre_buffer)
        post = list(self._post_buffer) if self._post_buffer is not None else []
        self._post_buffer = None

        all_frames = pre + post
        if not all_frames:
            logger.warning("No frames in buffer for %s", camera_ip)
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{camera_ip.replace('.', '_')}.mp4"
        output_path = output_dir / filename

        sample_frame = all_frames[0][1]
        h, w = sample_frame.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, self.fps, (w, h))

        for _, frame in all_frames:
            writer.write(frame)

        writer.release()
        logger.info(
            "Clip saved: %s (%d frames, %ds pre + %ds post)",
            output_path, len(all_frames), self.pre_seconds, len(post) / self.fps,
        )
        return output_path
