from __future__ import annotations

import logging
import threading
import time

import cv2

from monitoramento_idoso.models import CameraInfo
from monitoramento_idoso.processing.detector import PersonDetector

logger = logging.getLogger(__name__)


DETECT_DEBOUNCE = 5


class CameraProcessor:
    def __init__(
        self,
        camera: CameraInfo,
        detector: PersonDetector,
        reconnect_delay: float = 2.0,
    ):
        self.camera = camera
        self.detector = detector
        self.reconnect_delay = reconnect_delay
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name=f"cam-{self.camera.ip}"
        )
        self._thread.start()
        logger.info("Processing started for %s", self.camera.ip)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Processing stopped for %s", self.camera.ip)

    def _get_rtsp_url(self) -> str | None:
        urls = self.camera.rtsp_urls
        if not urls:
            return None
        return next(iter(urls.values()))

    def _loop(self) -> None:
        rtsp_url = self._get_rtsp_url()
        if not rtsp_url:
            logger.error("No RTSP URL for %s — stopping", self.camera.ip)
            self._running = False
            return

        cap: cv2.VideoCapture | None = None
        person_seen = False
        detect_count = 0
        lost_count = 0

        while self._running:
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                logger.info("Connecting to %s ...", self.camera.ip)
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    logger.warning(
                        "Cannot connect to %s — retrying in %ss",
                        self.camera.ip,
                        self.reconnect_delay,
                    )
                    time.sleep(self.reconnect_delay)
                    continue
                logger.info("Connected to %s", self.camera.ip)

            ret, frame = cap.read()
            if not ret:
                logger.warning("Frame read failed from %s — reconnecting", self.camera.ip)
                cap.release()
                cap = None
                time.sleep(self.reconnect_delay)
                continue

            detections = self.detector.detect(frame)
            if detections:
                detect_count += 1
                lost_count = 0
            else:
                lost_count += 1
                detect_count = 0

            if not person_seen and detect_count >= DETECT_DEBOUNCE:
                person_seen = True
                logger.info(
                    "Person detected on %s (%d)",
                    self.camera.ip,
                    len(detections),
                )
            elif person_seen and lost_count >= DETECT_DEBOUNCE:
                person_seen = False
                logger.info("Person lost on %s", self.camera.ip)

        if cap is not None:
            cap.release()
