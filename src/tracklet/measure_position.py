"""measure_position — pixel -> sky (S5).

Contract: ``measure_position(streak, wcs) -> SkyCoord`` (ICRS). Reads NO truth. Lifts the streak's
sub-pixel ``.midpoint`` (x, y) to a sky position through the supplied WCS.

The WCS is an INPUT: in S5's tests it is the TRUE WCS (``render.build_truth_wcs``); in the real
pipeline it is the WCS blindly recovered by ``solve_pointing``. measure_position is agnostic to
which — it never reaches for the sealed scene answer, so the non-circularity seal is structural
(the signature is exactly ``(streak, wcs)``; the module imports no sealed-answer loader, never
names the sealed-answer artifact, and never imports the scoring module — pinned by
tests/test_measure_position.py, mirroring the solve_pointing / detect_streak seals).

Pixel convention: astropy's ``wcs.pixel_to_world`` uses the 0-based pixel convention, consistent
with ``build_truth_wcs`` (whose CRPIX is the 1-based FITS center) as used in S2/S3 with origin=0.
"""
from __future__ import annotations

from astropy.coordinates import SkyCoord


def measure_position(streak, wcs) -> SkyCoord:
    """Lift the streak midpoint (x, y) to an ICRS SkyCoord via ``wcs.pixel_to_world``.

    Parameters
    ----------
    streak
        Anything exposing a sub-pixel ``.midpoint`` of ``(x, y)`` pixel coordinates (a
        ``detect_streak.StreakDetection`` in the pipeline; any object with ``.midpoint`` in tests).
    wcs : astropy.wcs.WCS
        The world coordinate system to project through. The TRUE WCS in S5's tests, the
        blind-recovered WCS in the real pipeline — measure_position treats both identically.

    Returns
    -------
    astropy.coordinates.SkyCoord
        The sky position of the midpoint, in the ICRS frame.
    """
    x, y = streak.midpoint
    coord = wcs.pixel_to_world(x, y)
    return coord.icrs
