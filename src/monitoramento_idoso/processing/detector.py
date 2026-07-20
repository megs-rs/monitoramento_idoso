from __future__ import annotations

import logging
from dataclasses import dataclass

from ultralytics import YOLO

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float


class PersonDetector:
    def __init__(self, model_name: str = "yolo11n.pt", confidence: float = 0.5):
        self.confidence = confidence
        logger.info("Loading YOLO model: %s", model_name)
        self.model = YOLO(model_name)
        logger.info("Model loaded (confidence=%.2f)", confidence)

    def detect(self, frame) -> list[Detection]:
        results = self.model(frame, classes=[PERSON_CLASS_ID], verbose=False)
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < self.confidence:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append(
                    Detection(x1=x1, y1=y1, x2=x2, y2=y2, confidence=conf)
                )
        return detections
