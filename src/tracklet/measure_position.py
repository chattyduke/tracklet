"""measure_position — pixel -> sky (S5).

Contract: measure_position(streak, wcs) -> SkyCoord (ICRS). Reads NO truth. Streak-midpoint pixel
-> RA/Dec via the recovered WCS.
"""
from __future__ import annotations


def measure_position(streak, wcs) -> "SkyCoord":  # noqa: F821
    raise NotImplementedError("measure_position lands in Sprint 5")
