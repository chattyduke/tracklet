"""S4 detect_streak tests — ACs 4.1-4.4, all NON-solver, pure computer vision.

detect_streak is the pure-CV module: it sees ONLY the delivered, WCS-free ``image.fits`` and
recovers the satellite trail as a single merged line whose sub-pixel MIDPOINT (refined by a
1D-Gaussian transverse-profile fit) is what S5 will lift to RA/Dec. It reads NO truth.

The non-circularity guarantee is structural (AC 4.4: the signature has no truth path and the module
imports no truth loader / never names ``truth.json``) — exactly mirroring the solve_pointing seal.
Every test here renders the golden frame with the SAME idiom as test_render.py /
test_solve_pointing.py (build_scene -> load fixtures -> render_scene -> result.image_path /
result.truth_path), and the accuracy/single-streak tests MAY read truth to score the detection.

No solve-field, no network, no @solver mark: this whole file runs under ``pytest -m "not solver"``.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from astropy.io import fits
from astropy.stats import sigma_clipped_stats

from tracklet import detect_streak as ds_module
from tracklet.detect_streak import DetectFailure, StreakDetection, detect_streak
from tracklet.render import (
    _SKY_BACKGROUND_E,
    _add_noise,
    _render_stars,
    build_truth_wcs,
    render_scene,
)
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"

# --- AC 4.1 accuracy bound (chosen from FIRST PRINCIPLES, before measuring) -------------------
# The reported midpoint is the AVERAGE of the two merged-line endpoints, refined transversely by a
# 1D-Gaussian fit to the perpendicular intensity profile. Error budget:
#   * Each Hough endpoint carries ~PSF-width + 1px raster quantization (~2-3 px) of LONGITUDINAL
#     slide along the trail. But the midpoint averages the two endpoints, and a symmetric trail's
#     geometric center is fixed regardless of how far each endpoint slid inward -> longitudinal
#     slide largely cancels in the midpoint.
#   * The TRANSVERSE position is then driven sub-pixel by the 1D-Gaussian normal-profile fit
#     (sigma ~ 1.5 px PSF, high SNR -> centroid precision << 1 px).
# A conservative single-digit engineering ceiling that comfortably covers residual asymmetry +
# fit noise, yet is far tighter than the ~half-trail error a mis-merge would produce, is 5 px.
_MIDPOINT_TOL_PX = 5.0


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


@pytest.fixture(scope="module")
def catalogue(scene):
    return load_catalogue(default_catalogue_path(scene))


@pytest.fixture(scope="module")
def tle(scene):
    return load_tle(default_tle_path(scene))


@pytest.fixture(scope="module")
def golden(scene, catalogue, tle, tmp_path_factory):
    """Render the golden scene ONCE -> the delivered image.fits + sealed truth.json.

    detect_streak is given ONLY image.fits; truth.json is read here in the TEST (the accuracy and
    single-streak tests MAY read truth) to score the detection. Same render idiom as
    test_render.py / test_solve_pointing.py.
    """
    out = tmp_path_factory.mktemp("golden_streak")
    return render_scene(scene, catalogue, tle, out)


# ---------------------------------------------------------------------------
# AC 4.1 — accuracy: detected midpoint matches truth's exposure-MIDPOINT pixel.
# ---------------------------------------------------------------------------


def test_detected_midpoint_matches_truth_midpoint(golden):
    """The merged-streak midpoint lands within _MIDPOINT_TOL_PX of truth's satellite_px['mid'].

    Reads truth ONLY to score (sealed midpoint = the exposure-midpoint pixel, the point S5
    recovers). Prints the actual residual so the chosen bound can be judged against reality.
    """
    result = detect_streak(str(golden.image_path))
    assert isinstance(result, StreakDetection), f"expected a StreakDetection, got {result!r}"

    truth = json.loads(golden.truth_path.read_text())
    truth_mid = np.array(truth["satellite_px"]["mid"], dtype=float)

    detected = np.array(result.midpoint, dtype=float)
    residual = float(np.hypot(*(detected - truth_mid)))
    print(f"\n[AC 4.1] detected midpoint={tuple(round(v, 3) for v in detected)} "
          f"truth midpoint={tuple(round(v, 3) for v in truth_mid)} "
          f"residual={residual:.4f} px (bound N={_MIDPOINT_TOL_PX} px)")
    assert residual < _MIDPOINT_TOL_PX, (
        f"detected midpoint off by {residual:.3f} px (tol {_MIDPOINT_TOL_PX} px)"
    )


# ---------------------------------------------------------------------------
# AC 4.2 — single streak: the collinear Hough fragments are MERGED into exactly one streak.
# ---------------------------------------------------------------------------


def _raw_hough_segments(image_path):
    """Re-run the detector's front-end (background-subtract -> robust uint8 -> Canny -> HoughLinesP)
    to obtain the RAW segment list — the same fragments detect_streak must merge into one streak.
    """
    data = fits.getdata(image_path).astype(np.float64)
    _, median, std = sigma_clipped_stats(data, sigma=3.0)
    sub = data - median
    hi = 30.0 * std if std > 0 else 1.0
    scaled = np.clip(sub / hi * 255.0, 0.0, 255.0).astype(np.uint8)
    edges = cv2.Canny(scaled, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=150, maxLineGap=20)
    return [] if lines is None else [tuple(map(float, l[0])) for l in lines]


def test_collinear_fragments_merge_to_single_streak(golden):
    """Raw HoughLinesP yields >1 collinear fragment along the trail; detect merges them into ONE.

    This is a real assertion about the merge step: the front-end produces multiple segments spread
    along the single physical trail, and detect_streak returns ONE streak whose endpoints span the
    full extent of those fragments (not one of the short raw segments).
    """
    raw = _raw_hough_segments(golden.image_path)
    assert len(raw) > 1, (
        f"precondition: raw HoughLinesP should fragment the trail into >1 segment, got {len(raw)}"
    )
    # All raw fragments lie along ONE physical trail -> share an angle (mod 180).
    angles = np.array([np.degrees(np.arctan2(s[3] - s[1], s[2] - s[0])) % 180.0 for s in raw])
    assert angles.std() < 5.0, f"raw fragments not collinear (angle std {angles.std():.1f} deg)"

    result = detect_streak(str(golden.image_path))
    assert isinstance(result, StreakDetection), f"expected a StreakDetection, got {result!r}"

    # The single merged streak spans the full extent of the raw fragments: its length must reach
    # the longest collinear run, i.e. exceed the longest single raw fragment.
    raw_lengths = [np.hypot(s[2] - s[0], s[3] - s[1]) for s in raw]
    (ex0, ey0), (ex1, ey1) = result.endpoints
    merged_len = float(np.hypot(ex1 - ex0, ey1 - ey0))
    assert merged_len >= max(raw_lengths) - 1.0, (
        f"merged streak length {merged_len:.1f} px did not reach the longest raw fragment "
        f"{max(raw_lengths):.1f} px — fragments were not merged"
    )
    # And the merged streak's angle matches the common fragment angle.
    merged_ang = np.degrees(np.arctan2(ey1 - ey0, ex1 - ex0)) % 180.0
    da = abs(merged_ang - float(np.median(angles)))
    da = min(da, 180.0 - da)
    assert da < 5.0, f"merged angle {merged_ang:.1f} deg disagrees with fragments {np.median(angles):.1f} deg"


# ---------------------------------------------------------------------------
# AC 4.3 — honest failure: a stars+noise frame with NO trail RETURNS a DetectFailure (not raised,
# not a fabricated streak). Fair fixture: realistic stars + background + read noise, no line.
# ---------------------------------------------------------------------------


def _render_stars_and_noise_only(scene, catalogue, out_path):
    """Build a FAIR no-streak FITS: render's OWN star field + sky + read-noise, but NEVER call
    _render_streak — so the satellite trail is genuinely absent while everything else (background
    level, read-noise sigma, star PSF) matches the golden scene exactly. Reuses render's star
    renderer + noise model so the fixture cannot be accused of being a trivially clean field.
    """
    wcs = build_truth_wcs(scene)
    signal = np.full((scene.height_px, scene.width_px), _SKY_BACKGROUND_E, dtype=np.float64)
    n_stars = _render_stars(signal, scene, catalogue, wcs)  # stars only — NO _render_streak
    image = _add_noise(signal, scene).astype(np.float32)
    fits.PrimaryHDU(data=image).writeto(out_path, overwrite=True)
    return n_stars, image


def test_no_streak_frame_returns_detectfailure_not_raise(scene, catalogue, tmp_path):
    image_path = tmp_path / "stars_no_streak.fits"
    n_stars, image = _render_stars_and_noise_only(scene, catalogue, image_path)

    # Fixture-fairness witnesses: the frame genuinely contains many stars over a real noisy
    # background (not a blank field), yet has NO satellite trail.
    assert n_stars > 100, f"unfair fixture: too few stars in frame ({n_stars})"
    _, median, std = sigma_clipped_stats(image.astype(np.float64), sigma=3.0)
    assert std > 0, "unfair fixture: no background noise present"
    assert float(image.max()) > median + 5 * std, "unfair fixture: no stars rise above the noise"

    result = detect_streak(str(image_path))
    assert isinstance(result, DetectFailure), (
        f"a star-only frame must RETURN a DetectFailure, got {result!r} (no fabricated streak)"
    )
    assert result.reason, "DetectFailure must carry a non-empty human-readable reason"


# ---------------------------------------------------------------------------
# AC 4.4 — sealed signature: detect_streak takes ONLY image_path and references no truth.
# ---------------------------------------------------------------------------


def test_signature_takes_only_image_path():
    params = list(inspect.signature(detect_streak).parameters)
    assert params == ["image_path"], params


def test_module_does_not_reference_truth():
    """AST/source scan: detect_streak never imports the truth loader nor names truth.json.

    A detector that reached for the sealed truth would silently destroy the non-circularity
    argument. Catch it structurally rather than trusting the runtime path. Mirrors
    test_solve_pointing.test_module_does_not_reference_truth.
    """
    source = Path(ds_module.__file__).read_text()
    assert "truth.json" not in source
    assert "_load_truth" not in source

    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            imported += [f"{mod}.{alias.name}" for alias in node.names]
    for forbidden in ("score", "tracklet.score"):
        assert not any(
            name == forbidden or name.endswith("." + forbidden) for name in imported
        ), f"detect_streak must not import {forbidden}: imports={imported}"
