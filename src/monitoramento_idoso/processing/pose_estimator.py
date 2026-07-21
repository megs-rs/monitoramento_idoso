from __future__ import annotations

import logging
from dataclasses import dataclass

import mediapipe as mp

logger = logging.getLogger(__name__)

mp_pose = mp.solutions.pose


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
        self.pose = mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            model_complexity=0,
        )

    def estimate(self, frame) -> PoseData:
        rgb = frame[:, :, ::-1]
        results = self.pose.process(rgb)

        if not results.pose_landmarks:
            return PoseData()

        lm = results.pose_landmarks.landmark

        def get_point(landmark):
            return (landmark.x, landmark.y)

        left_wrist = get_point(lm[mp_pose.PoseLandmark.LEFT_WRIST])
        right_wrist = get_point(lm[mp_pose.PoseLandmark.RIGHT_WRIST])
        left_shoulder = get_point(lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
        right_shoulder = get_point(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])
        left_hip = get_point(lm[mp_pose.PoseLandmark.LEFT_HIP])
        right_hip = get_point(lm[mp_pose.PoseLandmark.RIGHT_HIP])

        all_visible = all(
            p is not None and p[0] > 0 and p[1] > 0
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
        if hasattr(self, "pose"):
            self.pose.close()
