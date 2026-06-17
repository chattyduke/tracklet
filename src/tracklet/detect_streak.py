"""detect_streak — streak detection (S4).

Contract: detect_streak(image_path) -> StreakDetection | DetectFailure. Reads NO truth.
Canny + HoughLinesP -> merged streak; midpoint refined by a 1D-Gaussian transverse-profile fit
(NOT a 2D centroid).
"""
from __future__ import annotations


def detect_streak(image_path: str) -> "StreakDetection | DetectFailure":  # noqa: F821
    raise NotImplementedError("detect_streak lands in Sprint 4")
