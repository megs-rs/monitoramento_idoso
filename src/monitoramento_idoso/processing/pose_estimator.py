from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

mp_tasks = mp.tasks
mp_vision = mp_tasks.vision

_MODEL_PATH = Path(__file__).parent.parent.parent.parent / "models" / "pose_landmarker_lite.task"


@dataclass
class PoseData:
    left_wrist: tuple[float, float] | None = None
    right_wrist: tuple[float, float] | None = None
    left_shoulder: tuple[float, float] | None = None
    right_shoulder: tuple[float, float] | None = None
    left_hip: tuple[float, float] | None = None
    right_hip: tuple[float, float] | None = None
    visible: bool = False
    arms_raised: bool = False


class PoseEstimator:
    def __init__(self, min_detection_confidence: float = 0.5):
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Pose model not found at {_MODEL_PATH}. "
                "Download it from https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker"
            )

        base_options = mp_tasks.BaseOptions(model_asset_path=str(_MODEL_PATH))
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.IMAGE,
            min_pose_detection_confidence=min_detection_confidence,
            num_poses=1,
        )
        self.pose_landmarker = mp_vision.PoseLandmarker.create_from_options(options)

    def estimate(self, frame) -> PoseData:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self.pose_landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return PoseData()

        landmarks = result.pose_landmarks[0]

        def get_point(idx: int):
            lm = landmarks[idx]
            return (lm.x, lm.y)

        left_wrist = get_point(15)
        right_wrist = get_point(16)
        left_shoulder = get_point(11)
        right_shoulder = get_point(12)
        left_hip = get_point(23)
        right_hip = get_point(24)

        all_visible = all(
            p[0] > 0 and p[1] > 0
            for p in [left_wrist, right_wrist, left_shoulder, right_shoulder, left_hip, right_hip]
        )

        arms_raised = False
        if all_visible:
            avg_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
            left_raised = left_wrist[1] < avg_shoulder_y
            right_raised = right_wrist[1] < avg_shoulder_y
            arms_raised = left_raised or right_raised

        return PoseData(
            left_wrist=left_wrist,
            right_wrist=right_wrist,
            left_shoulder=left_shoulder,
            right_shoulder=right_shoulder,
            left_hip=left_hip,
            right_hip=right_hip,
            visible=all_visible,
            arms_raised=arms_raised,
        )

    def __del__(self):
        if hasattr(self, "pose_landmarker"):
            self.pose_landmarker.close()
