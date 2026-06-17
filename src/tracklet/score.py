"""score — arcsecond residual vs sealed truth (S5).

Contract: score(measured, truth_path) -> ScoreResult. The ONLY reader of truth.json besides the
render-writer (`score._load_truth` is the sole loader). arcsec via SkyCoord.separation.
"""
from __future__ import annotations


def score(measured, truth_path: str) -> "ScoreResult":  # noqa: F821
    raise NotImplementedError("score lands in Sprint 5")
