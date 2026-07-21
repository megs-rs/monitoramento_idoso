from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import cv2

from monitoramento_idoso.events.clip_recorder import ClipRecorder
from monitoramento_idoso.events.database import EventDatabase
from monitoramento_idoso.events.models import Event
from monitoramento_idoso.events.notifier import TelegramNotifier
from monitoramento_idoso.models import CameraInfo
from monitoramento_idoso.processing.detector import PersonDetector
from monitoramento_idoso.processing.pose_estimator import PoseEstimator

logger = logging.getLogger(__name__)


DETECT_DEBOUNCE = 5
ARMS_RAISED_DEBOUNCE = 10


class CameraProcessor:
    def __init__(
        self,
        camera: CameraInfo,
        detector: PersonDetector,
        pose_estimator: PoseEstimator | None = None,
        database: EventDatabase | None = None,
        notifier: TelegramNotifier | None = None,
        clip_recorder: ClipRecorder | None = None,
        reconnect_delay: float = 2.0,
    ):
        self.camera = camera
        self.detector = detector
        self.pose_estimator = pose_estimator
        self.database = database
        self.notifier = notifier
        self.clip_recorder = clip_recorder or ClipRecorder()
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

    def _trigger_event(self, event_type: str, frame) -> None:
        clip_path = self.clip_recorder.save(self.camera.ip)

        if self.database:
            event = Event(
                camera_ip=self.camera.ip,
                event_type=event_type,
                clip_path=str(clip_path) if clip_path else "",
            )
            self.database.insert(event)

        if self.notifier:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(
                        self.notifier.send_alert(self.camera.ip, event_type, clip_path)
                    )
                else:
                    loop.run_until_complete(
                        self.notifier.send_alert(self.camera.ip, event_type, clip_path)
                    )
            except RuntimeError:
                asyncio.run(
                    self.notifier.send_alert(self.camera.ip, event_type, clip_path)
                )

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
        arms_raised_count = 0
        arms_raised_seen = False
        frame_count = 0

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

            self.clip_recorder.add_frame(frame)
            frame_count += 1

            if frame_count % 450 == 0:
                logger.debug("Processing %s — %d frames processed", self.camera.ip, frame_count)

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
                arms_raised_seen = False
                arms_raised_count = 0

            if person_seen and self.pose_estimator:
                pose = self.pose_estimator.estimate(frame)
                if frame_count % 30 == 0:
                    logger.debug(
                        "Pose on %s — visible=%s arms_raised=%s",
                        self.camera.ip, pose.visible, pose.arms_raised,
                    )
                if pose.visible and pose.arms_raised:
                    arms_raised_count += 1
                else:
                    arms_raised_count = 0

                if not arms_raised_seen and arms_raised_count >= ARMS_RAISED_DEBOUNCE:
                    arms_raised_seen = True
                    logger.info("Arms raised on %s", self.camera.ip)
                    self._trigger_event("arms_raised", frame)

        if cap is not None:
            cap.release()
