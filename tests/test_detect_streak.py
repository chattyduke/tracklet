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
from tracklet.detect_streak import (
    _CANNY_HIGH,
    _CANNY_LOW,
    _HOUGH_MAX_LINE_GAP,
    _HOUGH_MIN_LINE_LENGTH,
    _HOUGH_THRESHOLD,
    _SCALE_SIGMA,
    _merge_collinear,
    _refine_midpoint_transverse,
    DetectFailure,
    StreakDetection,
    detect_streak,
)
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

    References the MODULE's own constants (not hardcoded copies) so this reference front-end can
    never silently diverge from the production detector if the CV parameters are ever tuned.
    """
    data = fits.getdata(image_path).astype(np.float64)
    _, median, std = sigma_clipped_stats(data, sigma=3.0)
    sub = data - median
    hi = _SCALE_SIGMA * std if std > 0 else 1.0
    scaled = np.clip(sub / hi * 255.0, 0.0, 255.0).astype(np.uint8)
    edges = cv2.Canny(scaled, _CANNY_LOW, _CANNY_HIGH)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=_HOUGH_THRESHOLD,
        minLineLength=_HOUGH_MIN_LINE_LENGTH,
        maxLineGap=_HOUGH_MAX_LINE_GAP,
    )
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

    # On the golden frame this is a COHERENCE check: detect returns ONE streak spanning at least the
    # longest collinear run, at the common fragment angle. The golden frame's Hough fragmentation is
    # mild (one near-full-length fragment), so the RIGOROUS proof that the merge reconstructs a trail
    # from MANY short fragments — and that a no-merge detector (return the longest single fragment)
    # FAILS — lives in test_detect_reconstructs_fragmented_trail + test_merge_collinear_unit below,
    # which control the fragmentation rather than depending on what Hough happens to emit here.
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


# ---------------------------------------------------------------------------
# AC 4.2 (rigorous, unit) — the merge geometry is load-bearing on CONTROLLED input, independent of
# whatever HoughLinesP happens to emit on the golden frame.
# ---------------------------------------------------------------------------


def test_merge_collinear_unit():
    """_merge_collinear collapses several collinear fragments into ONE streak spanning their FULL
    extent (far beyond the longest single fragment) and ignores an off-line decoy.

    This is the direct proof that the merge is not a pass-through: three fragments along y=500
    spanning x in [100, 900] (longest single = 250 px) must merge to a ~800 px streak.
    """
    frags = [
        (100.0, 500.0, 280.0, 500.0),  # len 180
        (350.0, 500.0, 600.0, 500.0),  # len 250
        (650.0, 500.0, 900.0, 500.0),  # len 250
        (120.0, 200.0, 300.0, 200.0),  # DECOY: same angle, different offset (y=200) -> excluded
    ]
    merged = _merge_collinear(frags)
    assert merged is not None
    p0, p1, angle_deg, span = merged
    assert span == pytest.approx(800.0, abs=1.0), f"merged span {span:.1f} px != full extent ~800"
    xs = sorted([p0[0], p1[0]])
    assert xs[0] == pytest.approx(100.0, abs=1.0) and xs[1] == pytest.approx(900.0, abs=1.0)
    assert min(p0[1], p1[1]) == pytest.approx(500.0, abs=1.0)  # on the y=500 line, NOT the y=200 decoy
    assert angle_deg == pytest.approx(0.0, abs=1.0)
    assert _merge_collinear([]) is None  # empty input -> None (defensive contract)


def _write_fragmented_trail_fits(
    path, *, shape=(600, 600), y0=300.0, sky=200.0, peak=500.0, sigma_t=1.5, read=5.0, seed=0
):
    """Synthetic frame: background + read noise + a horizontal Gaussian ridge broken into THREE
    dashes with gaps wider than the detector's maxLineGap, so Hough emits separate short segments.
    The full trail spans ~530 px; the longest single dash is ~160 px — so only a real merge reaches
    the full span. No truth.json (detect never reads truth). Deterministic (seeded RNG).

    `peak` is kept in the REAL rendered streak's saturation regime (sub-peak ~a few x the robust
    uint8 scale ceiling) so the bright bar's Canny edges fall within the detector's merge tolerance —
    a saturated wide bar (edges > the merge offset tol apart) would be unrepresentative of the
    actual ~1500-e streak the pipeline detects (whose golden-frame residual is 0.32 px)."""
    rng = np.random.default_rng(seed)
    img = np.full(shape, sky, dtype=np.float64)
    yy = np.arange(shape[0])[:, None].astype(np.float64)
    ridge = peak * np.exp(-((yy - y0) ** 2) / (2.0 * sigma_t ** 2))  # (H,1) transverse profile
    dashes = [(50, 210), (235, 395), (420, 580)]  # 160 px dashes, 25 px gaps (> maxLineGap=20)
    for xa, xb in dashes:
        img[:, xa:xb] += ridge
    img += rng.normal(0.0, read, size=shape)
    fits.PrimaryHDU(data=img.astype(np.float32)).writeto(path, overwrite=True)
    return dashes


def test_detect_reconstructs_fragmented_trail(tmp_path):
    """End-to-end merge proof: a deliberately FRAGMENTED trail (Hough emits several short collinear
    segments, none near full length) is reconstructed by detect_streak into ONE full-span streak.

    A no-merge detector that returned the longest single Hough fragment would fail the length
    assertion (longest dash ~160 px vs full span ~530 px) — so this pins AC 4.2 robustly.
    """
    image_path = tmp_path / "fragmented_trail.fits"
    dashes = _write_fragmented_trail_fits(image_path)
    full_span = dashes[-1][1] - dashes[0][0]  # 580 - 50 = 530 px

    raw = _raw_hough_segments(image_path)
    assert len(raw) > 1, f"precondition: expected the dashed trail to fragment, got {len(raw)} segs"
    assert max(np.hypot(s[2] - s[0], s[3] - s[1]) for s in raw) < 0.6 * full_span, (
        "precondition: no single raw fragment should approach the full trail span"
    )

    result = detect_streak(str(image_path))
    assert isinstance(result, StreakDetection), f"expected a StreakDetection, got {result!r}"
    assert result.length_px > 0.85 * full_span, (
        f"merged length {result.length_px:.1f} px did not reconstruct the full ~{full_span} px trail "
        f"— the merge step is not load-bearing (a no-merge detector would land here)"
    )
    mx, my = result.midpoint
    assert abs(mx - 315.0) < 5.0, f"midpoint x {mx:.1f} not near the trail center 315"
    assert abs(my - 300.0) < 3.0, f"midpoint y {my:.1f} not near the trail center 300"


# ---------------------------------------------------------------------------
# Transverse refinement — the 1D-Gaussian normal-profile fit is load-bearing (NOT a 2D centroid,
# NOT a no-op): it recovers a known sub-pixel transverse offset.
# ---------------------------------------------------------------------------


def test_transverse_refinement_recovers_subpixel_offset():
    """_refine_midpoint_transverse shifts the midpoint along the streak NORMAL onto the true
    sub-pixel transverse center. A no-op (return the geometric point) or a method that ignored the
    profile would not recover a known 0.35 px offset.
    """
    H = W = 64
    y_true = 31.35  # true transverse center of a horizontal ridge (angle 0 -> normal is vertical)
    yy = np.arange(H)[:, None].astype(np.float64)
    sub = (1000.0 * np.exp(-((yy - y_true) ** 2) / (2.0 * 1.5 ** 2))) * np.ones((1, W))
    geom_mid = (32.0, 31.0)  # geometric midpoint, transversely off the true center by 0.35 px
    rx, ry = _refine_midpoint_transverse(sub, geom_mid, angle_deg=0.0)
    assert abs(ry - y_true) < 0.1, f"refined y {ry:.3f} did not recover true center {y_true}"
    assert abs(ry - geom_mid[1]) > 0.2, "refinement was a no-op (did not move toward the true center)"
    assert rx == pytest.approx(geom_mid[0], abs=1e-6), "longitudinal x must be unchanged (angle 0)"
