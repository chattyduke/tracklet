"""detect_streak — streak detection (S4).

Contract: ``detect_streak(image_path) -> StreakDetection | DetectFailure``. Reads NO truth.

Pipeline (the locked S4 design brief):

    image.fits
      -> sigma-clipped background subtract (astropy.stats.sigma_clipped_stats)
      -> robustly scale to uint8 (clip at a sigma-multiple of the background — robust to the bright
         star population, unlike a hard percentile which saturates a star-dense field)
      -> cv2.Canny edge detect
      -> cv2.HoughLinesP                     (returns MANY short fragments along the one trail)
      -> cluster/merge COLLINEAR fragments into ONE streak (the ISS trail is a single long line:
         group fragments by angle similarity + perpendicular-offset proximity, keep the cluster
         with the largest collinear SPAN, take its extreme endpoints as the merged endpoints)
      -> measured point = MIDPOINT of the merged line
      -> refine the midpoint TRANSVERSELY by a 1D-Gaussian fit to the PERPENDICULAR intensity
         profile (sample the background-subtracted image along the streak NORMAL at the midpoint,
         fit a 1D Gaussian, take its center for the sub-pixel transverse position). This is a 1D
         transverse fit, NOT a 2D centroid (a 2D centroid is wrong for an elongated feature).

Returns a frozen ``StreakDetection`` on success, or a frozen ``DetectFailure`` (RETURNED, never
raised) when no single coherent trail is found. The signature is ``(image_path)`` only — no truth
path — and the module imports no truth loader and never names the sealed-truth artifact, so the
non-circularity seal is structural (pinned by tests/test_detect_streak.py AC 4.4), exactly as in
solve_pointing. Deterministic: every operation (sigma-clip, Canny, Hough, the merge, the curve fit)
is deterministic for a given image; no RNG is used.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from scipy.optimize import curve_fit

# --- detector parameters (deterministic; documented so the CV pipeline is auditable) ----------
# Robust uint8 scaling: map [0, _SCALE_SIGMA * background_std] -> [0, 255]. A sigma-multiple (NOT a
# hard high percentile) is robust to a star-DENSE field: on the golden frame ~5000 stars sit above
# the sky, so a 99.9-percentile reference collapses to a low value and saturates the whole field to
# white, drowning the trail in spurious edges. Clipping at 30 sigma keeps stars + the trail as crisp
# bright features against a clean background, so Canny/Hough see the trail and almost nothing else.
_SCALE_SIGMA = 30.0
# Canny hysteresis thresholds (on the uint8 scaled image).
_CANNY_LOW, _CANNY_HIGH = 50, 150
# HoughLinesP parameters: 1px / 1deg accumulator, a vote threshold and a minimum line length that
# keep only substantial linear runs, with a modest gap tolerance so a fragmented trail still votes.
_HOUGH_THRESHOLD = 50
_HOUGH_MIN_LINE_LENGTH = 150
_HOUGH_MAX_LINE_GAP = 20
# Collinearity tolerances for merging fragments into one streak: same orientation within this angle
# (degrees, mod 180) AND the same line within this perpendicular offset (pixels).
_MERGE_ANGLE_TOL_DEG = 3.0
_MERGE_OFFSET_TOL_PX = 8.0
# A real trail must span at least this many pixels (collinear extent of the merged cluster). Below
# this we have only incidental clutter, not a satellite trail -> DetectFailure. The golden trail
# spans ~1370 px; a star-only frame yields no Hough segments at all. 100 px is a wide, safe floor.
_MIN_STREAK_SPAN_PX = 100.0
# Transverse profile sampling for the 1D-Gaussian midpoint refinement: sample the normal profile
# from -_PROFILE_HALF..+_PROFILE_HALF px about the midpoint at _PROFILE_STEP spacing (bilinear).
_PROFILE_HALF = 8.0
_PROFILE_STEP = 0.5


@dataclass(frozen=True)
class StreakDetection:
    """A single satellite trail recovered from one frame (pixel space only — NO sky coords).

    Attributes
    ----------
    midpoint : tuple[float, float]
        Sub-pixel ``(x, y)`` center of the merged trail, transversely refined by the 1D-Gaussian
        normal-profile fit. THIS is the point S5 lifts to RA/Dec via the recovered WCS.
    endpoints : tuple[tuple[float, float], tuple[float, float]]
        The two ``(x, y)`` extreme endpoints of the merged trail (the collinear cluster's extent).
    angle_deg : float
        Orientation of the trail in degrees, ``atan2(dy, dx)`` taken mod 180 (a line has no head/
        tail), in image pixel axes.
    length_px : float
        Euclidean distance between the two endpoints (the merged trail length in pixels).
    """

    midpoint: tuple[float, float]
    endpoints: tuple[tuple[float, float], tuple[float, float]]
    angle_deg: float
    length_px: float


@dataclass(frozen=True)
class DetectFailure:
    """No single coherent trail was found. RETURNED, never raised.

    Attributes
    ----------
    reason : str
        Human-readable explanation of why detection did not yield a streak.
    """

    reason: str


# ---------------------------------------------------------------------------
# Front-end: image -> background-subtracted float + the raw Hough fragments
# ---------------------------------------------------------------------------


def _load_and_subtract(image_path: str) -> tuple[np.ndarray, float]:
    """Load image.fits, sigma-clip the background, return (background-subtracted image, bg std)."""
    data = np.asarray(fits.getdata(image_path), dtype=np.float64)
    _, median, std = sigma_clipped_stats(data, sigma=3.0)
    return data - float(median), float(std)


def _hough_fragments(sub: np.ndarray, std: float) -> list[tuple[float, float, float, float]]:
    """Robust uint8 scale -> Canny -> HoughLinesP. Returns the raw segment list (possibly empty)."""
    hi = _SCALE_SIGMA * std if std > 0 else 1.0
    scaled = np.clip(sub / hi * 255.0, 0.0, 255.0).astype(np.uint8)
    edges = cv2.Canny(scaled, _CANNY_LOW, _CANNY_HIGH)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180.0,
        threshold=_HOUGH_THRESHOLD,
        minLineLength=_HOUGH_MIN_LINE_LENGTH,
        maxLineGap=_HOUGH_MAX_LINE_GAP,
    )
    if lines is None:
        return []
    return [tuple(float(v) for v in line[0]) for line in lines]


# ---------------------------------------------------------------------------
# Merge: collapse collinear fragments into one streak (extreme endpoints of the densest cluster)
# ---------------------------------------------------------------------------


def _segment_angle_offset(seg: tuple[float, float, float, float]) -> tuple[float, float]:
    """(orientation in radians mod pi, signed perpendicular offset of the line from the origin)."""
    x1, y1, x2, y2 = seg
    ang = np.arctan2(y2 - y1, x2 - x1) % np.pi
    nx, ny = -np.sin(ang), np.cos(ang)  # unit normal
    offset = x1 * nx + y1 * ny
    return float(ang), float(offset)


def _merge_collinear(
    segments: list[tuple[float, float, float, float]],
) -> tuple[tuple[float, float], tuple[float, float], float, float] | None:
    """Cluster collinear fragments; return the largest-span cluster's (p0, p1, angle_deg, span).

    The ISS trail is ONE long line broken by Hough into many fragments. For each fragment we seed a
    cluster of all fragments matching it in orientation (mod 180, within _MERGE_ANGLE_TOL_DEG) and
    perpendicular offset (within _MERGE_OFFSET_TOL_PX), then take the cluster with the greatest
    collinear SPAN (projection extent along its axis). The merged endpoints are that cluster's two
    extreme projected points. Returns None if there are no fragments.
    """
    if not segments:
        return None

    props = [_segment_angle_offset(s) for s in segments]
    ang_tol = np.deg2rad(_MERGE_ANGLE_TOL_DEG)
    best: tuple[float, tuple[float, float], tuple[float, float], float] | None = None

    for (ai, oi) in props:
        members = [
            seg
            for seg, (aj, oj) in zip(segments, props)
            if min(abs(aj - ai), np.pi - abs(aj - ai)) <= ang_tol
            and abs(oj - oi) <= _MERGE_OFFSET_TOL_PX
        ]
        ux, uy = np.cos(ai), np.sin(ai)  # unit vector along the cluster axis
        pts = np.array(
            [p for seg in members for p in ((seg[0], seg[1]), (seg[2], seg[3]))], dtype=float
        )
        proj = pts[:, 0] * ux + pts[:, 1] * uy
        lo_i, hi_i = int(np.argmin(proj)), int(np.argmax(proj))
        span = float(proj[hi_i] - proj[lo_i])
        p0 = (float(pts[lo_i, 0]), float(pts[lo_i, 1]))
        p1 = (float(pts[hi_i, 0]), float(pts[hi_i, 1]))
        if best is None or span > best[0]:
            best = (span, p0, p1, ai)

    span, p0, p1, _ = best
    angle_deg = float(np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0)
    return p0, p1, angle_deg, span


# ---------------------------------------------------------------------------
# Transverse refinement: 1D-Gaussian fit to the perpendicular intensity profile at the midpoint
# ---------------------------------------------------------------------------


def _bilinear(img: np.ndarray, x: float, y: float) -> float:
    """Bilinear sample of img[y, x] with edge clamping (returns 0.0 fully out of bounds)."""
    h, w = img.shape
    if x < 0 or y < 0 or x > w - 1 or y > h - 1:
        return 0.0
    x0, y0 = int(np.floor(x)), int(np.floor(y))
    x1, y1 = min(x0 + 1, w - 1), min(y0 + 1, h - 1)
    fx, fy = x - x0, y - y0
    return float(
        img[y0, x0] * (1 - fx) * (1 - fy)
        + img[y0, x1] * fx * (1 - fy)
        + img[y1, x0] * (1 - fx) * fy
        + img[y1, x1] * fx * fy
    )


def _gaussian(x: np.ndarray, amp: float, mu: float, sigma: float, offset: float) -> np.ndarray:
    return amp * np.exp(-((x - mu) ** 2) / (2.0 * sigma * sigma)) + offset


def _refine_midpoint_transverse(
    sub: np.ndarray, midpoint: tuple[float, float], angle_deg: float
) -> tuple[float, float]:
    """Refine the midpoint along the streak NORMAL by a 1D-Gaussian fit to the transverse profile.

    Sample the (background-subtracted) intensity along the unit normal about the midpoint, fit a 1D
    Gaussian, and shift the midpoint by the fitted center ``mu`` along the normal. Falls back to the
    geometric midpoint if the fit fails or is implausibly off-profile (a robust no-op, never raises).
    """
    ang = np.deg2rad(angle_deg)
    nx, ny = -np.sin(ang), np.cos(ang)  # unit normal to the streak
    mx, my = midpoint
    ts = np.arange(-_PROFILE_HALF, _PROFILE_HALF + _PROFILE_STEP / 2.0, _PROFILE_STEP)
    profile = np.array([_bilinear(sub, mx + t * nx, my + t * ny) for t in ts])

    try:
        p0 = [float(profile.max() - np.median(profile)), 0.0, 1.5, float(np.median(profile))]
        popt, _ = curve_fit(_gaussian, ts, profile, p0=p0, maxfev=10000)
        mu = float(popt[1])
    except Exception:
        return (float(mx), float(my))

    # Reject a wild fit (center should sit inside the sampled window); else keep the geometric point.
    if not np.isfinite(mu) or abs(mu) > _PROFILE_HALF:
        return (float(mx), float(my))
    return (float(mx + mu * nx), float(my + mu * ny))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect_streak(image_path: str) -> "StreakDetection | DetectFailure":
    """Detect the single satellite trail in ``image_path`` (see module docstring for the pipeline).

    Parameters
    ----------
    image_path : str
        Path to the delivered, WCS-free ``image.fits``. NO truth path is accepted (the seal).

    Returns
    -------
    StreakDetection
        On success: the merged-trail endpoints, sub-pixel transversely-refined midpoint, orientation,
        and length.
    DetectFailure
        RETURNED (never raised) when no single coherent trail is found.
    """
    sub, std = _load_and_subtract(image_path)
    segments = _hough_fragments(sub, std)
    if not segments:
        return DetectFailure(reason="no linear features found (HoughLinesP returned no segments)")

    merged = _merge_collinear(segments)
    if merged is None:  # defensive; segments is non-empty here
        return DetectFailure(reason="no collinear fragment cluster could be formed")

    p0, p1, angle_deg, span = merged
    if span < _MIN_STREAK_SPAN_PX:
        return DetectFailure(
            reason=(
                f"longest collinear run spans only {span:.1f} px "
                f"(< {_MIN_STREAK_SPAN_PX:.0f} px floor) — no satellite trail"
            )
        )

    geom_mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
    midpoint = _refine_midpoint_transverse(sub, geom_mid, angle_deg)
    length_px = float(np.hypot(p1[0] - p0[0], p1[1] - p0[1]))
    return StreakDetection(
        midpoint=midpoint,
        endpoints=(p0, p1),
        angle_deg=angle_deg,
        length_px=length_px,
    )
