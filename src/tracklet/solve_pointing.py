"""solve_pointing — blind plate-solve (S3).

Contract: solve_pointing(image_path, scale_hint) -> SolveResult | SolveFailure. Reads NO truth —
signature takes the image only. Blind solve-field by default (no RA/Dec seed) -> astropy WCS.
"""
from __future__ import annotations


def solve_pointing(image_path: str, scale_hint) -> "SolveResult | SolveFailure":  # noqa: F821
    raise NotImplementedError("solve_pointing lands in Sprint 3")
