"""realgate — the AC-4.6 plausibility gate (anti wrong-field-lock) for the M1 real path.

A blind plate-solve can converge on the WRONG field and still hand back a numerically valid WCS.
Scoring the satellite against such a WCS would produce a *flattering* finite residual that means
nothing. AC 4.6 guards against this: a finite residual is trusted ONLY if the blind-recovered field
OVERLAPS the independently-known pointing field — i.e. the recovered WCS center agrees with the
expected pointing center to within ``0.5 x fov_deg`` (half the field width; the true field must
overlap the recovered field). A wider miss is reported as an HONEST TYPED failure (wrong asterism),
never a residual.

Non-circularity (load-bearing): the expected pointing center is NOT this frame's own
recovered-minus-commanded (that would be circular — it would always pass). For the DDOTI frame, which
carries no header WCS, the expected center is the commanded mount pointing (STRCURA/STRCUDE) plus a
FIXED camera offset derived NON-CIRCULARLY by blind-solving OTHER C1 frames of the same camera. This
module takes the already-derived expected center as an argument; it never reads truth and never feeds
anything back into the solver. The comparison is computed downstream of the solver from in-memory WCS
centers only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from astropy.coordinates import SkyCoord


@dataclass(frozen=True)
class PlausibilityResult:
    """Outcome of the AC-4.6 plausibility check.

    Attributes
    ----------
    ok : bool
        True iff the recovered field overlaps the expected field (separation <= tolerance).
    separation_deg : float
        Great-circle separation between the recovered WCS center and the expected pointing center.
    tolerance_deg : float
        The pinned tolerance applied (``0.5 * fov_deg``).
    recovered_center_deg : tuple[float, float]
        The recovered WCS center (RA, Dec) in degrees (for the report/diagnostic).
    expected_center_deg : tuple[float, float]
        The expected pointing center (RA, Dec) in degrees that the recovery was checked against.
    """

    ok: bool
    separation_deg: float
    tolerance_deg: float
    recovered_center_deg: "tuple[float, float]"
    expected_center_deg: "tuple[float, float]"


def wcs_center_radec(wcs, naxis1: int, naxis2: int) -> "tuple[float, float]":
    """Return the (RA, Dec) in degrees of the central pixel of an ``astropy.wcs.WCS``.

    The center pixel is ``((naxis1 - 1) / 2, (naxis2 - 1) / 2)`` in 0-based pixel coordinates. The
    WCS is used to project that pixel to world coordinates; nothing is read back into the solver.
    """
    cx = (float(naxis1) - 1.0) / 2.0
    cy = (float(naxis2) - 1.0) / 2.0
    sky = wcs.pixel_to_world(cx, cy)
    icrs = sky.icrs
    return float(icrs.ra.deg), float(icrs.dec.deg)


def check_field_overlap(
    recovered_center_deg: "tuple[float, float]",
    expected_center_deg: "tuple[float, float]",
    fov_deg: float,
) -> PlausibilityResult:
    """AC-4.6 plausibility gate: does the recovered field overlap the expected pointing field?

    Trusts the recovery ONLY when the angular separation between the recovered WCS center and the
    expected pointing center is ``<= 0.5 * fov_deg`` (the true field must overlap the recovered
    field). The separation is the rigorous great-circle distance (so it is correct near the poles and
    across the RA=0/360 wrap), not a naive RA/Dec difference.

    Parameters
    ----------
    recovered_center_deg : (float, float)
        The blind-recovered WCS center (RA, Dec), degrees — computed downstream of the solver.
    expected_center_deg : (float, float)
        The independently-known pointing center (RA, Dec), degrees. For DDOTI this is the commanded
        mount pointing plus the non-circularly-derived camera offset — NEVER this frame's own
        recovered-minus-commanded.
    fov_deg : float
        The field-of-view width in degrees; the tolerance is half of it.

    Returns
    -------
    PlausibilityResult
    """
    if not (isinstance(fov_deg, (int, float)) and fov_deg > 0.0):
        raise ValueError(f"fov_deg must be a positive number of degrees; got {fov_deg!r}")

    rec = SkyCoord(ra=recovered_center_deg[0], dec=recovered_center_deg[1], unit="deg")
    exp = SkyCoord(ra=expected_center_deg[0], dec=expected_center_deg[1], unit="deg")
    separation_deg = float(rec.separation(exp).deg)
    tolerance_deg = 0.5 * float(fov_deg)

    return PlausibilityResult(
        ok=bool(np.isfinite(separation_deg) and separation_deg <= tolerance_deg),
        separation_deg=separation_deg,
        tolerance_deg=tolerance_deg,
        recovered_center_deg=(float(recovered_center_deg[0]), float(recovered_center_deg[1])),
        expected_center_deg=(float(expected_center_deg[0]), float(expected_center_deg[1])),
    )
