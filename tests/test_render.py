"""S2 render tests — ACs 2.1-2.5, all OFFLINE against the committed frozen fixtures.

render is the KEYSTONE module: scene -> render -> image.fits (CLEAN, no WCS) + truth.json (SEALED).
These tests pin the load-bearing seal (image.fits WCS-free; render is the sole truth.json writer),
the WCS conventions (negative CD1_1 / origin=0 / FITS Y-flip), determinism, and streak geometry.

No network: every test consumes data/{tle,catalogue} via the scene loaders and writes only into a
pytest tmp_path. The @solver gate does not apply (render is pure-offline construction).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tracklet.render import RenderResult, build_truth_wcs, render_scene
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"

# WCS keywords that MUST NOT appear in the clean image.fits header (the load-bearing seal).
_WCS_KEYWORDS = ("CRVAL", "CD1_", "CD2_", "CTYPE", "CRPIX", "CDELT", "PC1_", "PC2_")


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


@pytest.fixture(scope="module")
def catalogue(scene):
    return load_catalogue(default_catalogue_path(scene))


@pytest.fixture(scope="module")
def tle(scene):
    return load_tle(default_tle_path(scene))


# ---------------------------------------------------------------------------
# AC 2.4 — WCS round-trip + the negative-CD1_1 / origin=0 / Y-flip conventions.
# This is where sign/flip bugs hide; exercise them as dedicated unit tests.
# ---------------------------------------------------------------------------


def test_truth_wcs_crval_is_scene_center(scene):
    wcs = build_truth_wcs(scene)
    crval = wcs.wcs.crval
    assert crval[0] == pytest.approx(scene.center_ra_deg)
    assert crval[1] == pytest.approx(scene.center_dec_deg)


def test_truth_wcs_is_tan_projection(scene):
    wcs = build_truth_wcs(scene)
    assert list(wcs.wcs.ctype) == ["RA---TAN", "DEC--TAN"]


def test_truth_wcs_crpix_at_frame_center(scene):
    # FITS CRPIX is 1-based; the center of an N-pixel axis is (N+1)/2.
    wcs = build_truth_wcs(scene)
    assert wcs.wcs.crpix[0] == pytest.approx((scene.width_px + 1) / 2.0)
    assert wcs.wcs.crpix[1] == pytest.approx((scene.height_px + 1) / 2.0)


def test_truth_wcs_cd1_1_is_negative(scene):
    # RA increases to the LEFT (east-left convention): CD1_1 must be negative,
    # magnitude == pixel scale in deg/px.
    wcs = build_truth_wcs(scene)
    cd = wcs.wcs.cd
    scale_deg = scene.pixel_scale_arcsec / 3600.0
    assert cd[0, 0] < 0
    assert cd[0, 0] == pytest.approx(-scale_deg)
    assert cd[1, 1] == pytest.approx(scale_deg)
    assert cd[0, 1] == pytest.approx(0.0)
    assert cd[1, 0] == pytest.approx(0.0)


def test_wcs_center_maps_to_central_pixel(scene):
    # crval at origin=0 must land on ((W-1)/2, (H-1)/2) = CRPIX - 1.
    wcs = build_truth_wcs(scene)
    x, y = wcs.wcs_world2pix(scene.center_ra_deg, scene.center_dec_deg, 0)
    assert float(x) == pytest.approx((scene.width_px - 1) / 2.0)
    assert float(y) == pytest.approx((scene.height_px - 1) / 2.0)


def test_wcs_ra_increases_left(scene):
    # Negative CD1_1 means a star EAST of center (larger RA) sits at a SMALLER x.
    wcs = build_truth_wcs(scene)
    cx, _ = wcs.wcs_world2pix(scene.center_ra_deg, scene.center_dec_deg, 0)
    east_x, _ = wcs.wcs_world2pix(
        scene.center_ra_deg + 0.1, scene.center_dec_deg, 0
    )
    assert float(east_x) < float(cx)


def test_wcs_dec_increases_up(scene):
    # Positive CD2_2 means a star NORTH of center (larger Dec) sits at a LARGER y
    # (FITS row 0 = bottom).
    wcs = build_truth_wcs(scene)
    _, cy = wcs.wcs_world2pix(scene.center_ra_deg, scene.center_dec_deg, 0)
    _, north_y = wcs.wcs_world2pix(
        scene.center_ra_deg, scene.center_dec_deg + 0.1, 0
    )
    assert float(north_y) > float(cy)


def test_wcs_round_trip_subpixel_grid(scene):
    # world2pix -> pix2world -> world2pix agrees within sub-pixel for a grid of points
    # spanning the frame, with origin=0 throughout.
    wcs = build_truth_wcs(scene)
    xs = np.linspace(0, scene.width_px - 1, 7)
    ys = np.linspace(0, scene.height_px - 1, 7)
    gx, gy = np.meshgrid(xs, ys)
    gx = gx.ravel()
    gy = gy.ravel()
    ra, dec = wcs.wcs_pix2world(gx, gy, 0)
    bx, by = wcs.wcs_world2pix(ra, dec, 0)
    assert np.max(np.abs(bx - gx)) < 1e-6
    assert np.max(np.abs(by - gy)) < 1e-6


# ---------------------------------------------------------------------------
# AC 2.1 — determinism: same seed -> byte-identical image array.
# ---------------------------------------------------------------------------


def _array_hash(arr: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


def test_render_is_deterministic_same_seed(scene, catalogue, tle, tmp_path):
    r1 = render_scene(scene, catalogue, tle, tmp_path / "a")
    r2 = render_scene(scene, catalogue, tle, tmp_path / "b")
    assert r1.image.shape == (scene.height_px, scene.width_px)
    assert r1.image.dtype == r2.image.dtype
    assert _array_hash(r1.image) == _array_hash(r2.image)


def test_render_differs_under_different_seed(scene, catalogue, tle, tmp_path):
    # A different seed must change the noise realisation (proves the RNG actually drives the image,
    # not a hard-coded array). Uses dataclasses.replace to avoid touching the frozen scene.
    import dataclasses

    other = dataclasses.replace(scene, seed=scene.seed + 1)
    r1 = render_scene(scene, catalogue, tle, tmp_path / "a")
    r2 = render_scene(other, catalogue, tle, tmp_path / "b")
    assert _array_hash(r1.image) != _array_hash(r2.image)


# ---------------------------------------------------------------------------
# AC 2.2 — clean-FITS seal: image.fits header has NO WCS keywords.
# ---------------------------------------------------------------------------


def test_image_fits_has_no_wcs_keywords(scene, catalogue, tle, tmp_path):
    from astropy.io import fits

    result = render_scene(scene, catalogue, tle, tmp_path)
    assert result.image_path.exists()
    with fits.open(result.image_path) as hdul:
        header = hdul[0].header
        keys = list(header.keys())
        for kw in _WCS_KEYWORDS:
            offenders = [k for k in keys if k.upper().startswith(kw)]
            assert not offenders, f"image.fits leaked WCS keyword(s) {offenders} (prefix {kw})"
        # Belt-and-braces: no WCS keyword card may appear ANYWHERE in the raw header text either
        # (catches a keyword smuggled into a COMMENT/HISTORY card). This is the load-bearing seal.
        raw = header.tostring().upper()
        for kw in _WCS_KEYWORDS:
            assert kw not in raw, f"image.fits raw header contains WCS token {kw!r}"


def test_image_fits_data_matches_rendered_array(scene, catalogue, tle, tmp_path):
    from astropy.io import fits

    result = render_scene(scene, catalogue, tle, tmp_path)
    with fits.open(result.image_path) as hdul:
        on_disk = hdul[0].data
    # FITS stores big-endian on disk; canonicalise to native float32 (the consumer-side normalise)
    # before the byte-level comparison. Values must be identical to RenderResult.image.
    on_disk_native = np.ascontiguousarray(on_disk.astype(np.float32))
    assert _array_hash(on_disk_native) == _array_hash(result.image)
    assert np.array_equal(on_disk, result.image)


# ---------------------------------------------------------------------------
# AC 2.3 — truth.json holds the injected truth (render is the SOLE writer).
# ---------------------------------------------------------------------------


def test_truth_json_written_and_well_formed(scene, catalogue, tle, tmp_path):
    result = render_scene(scene, catalogue, tle, tmp_path)
    assert result.truth_path.exists()
    truth = json.loads(result.truth_path.read_text())

    # WCS params
    wcs = truth["wcs"]
    assert wcs["ctype"] == ["RA---TAN", "DEC--TAN"]
    assert wcs["crval"][0] == pytest.approx(scene.center_ra_deg)
    assert wcs["crval"][1] == pytest.approx(scene.center_dec_deg)
    assert wcs["crpix"] == [
        pytest.approx((scene.width_px + 1) / 2.0),
        pytest.approx((scene.height_px + 1) / 2.0),
    ]
    cd = np.array(wcs["cd"])
    assert cd[0, 0] < 0

    # satellite sky positions (start / mid / end), midpoint is the scored truth
    sat = truth["satellite"]
    for key in ("start", "mid", "end"):
        assert "ra_deg" in sat[key] and "dec_deg" in sat[key]
    # scored truth convenience alias
    assert truth["scored_truth"]["ra_deg"] == pytest.approx(sat["mid"]["ra_deg"])
    assert truth["scored_truth"]["dec_deg"] == pytest.approx(sat["mid"]["dec_deg"])

    # satellite pixel endpoints + midpoint
    px = truth["satellite_px"]
    for key in ("start", "mid", "end"):
        assert len(px[key]) == 2

    # exposure window
    win = truth["exposure"]
    assert win["start_utc"] and win["mid_utc"] and win["end_utc"]
    assert win["exposure_s"] == pytest.approx(scene.exposure_s)

    # seed + catalogue ref
    assert truth["seed"] == scene.seed
    assert truth["catalogue_ref"]


def test_truth_wcs_matches_rendered_wcs(scene, catalogue, tle, tmp_path):
    # the WCS params sealed into truth.json must equal the WCS render actually used.
    result = render_scene(scene, catalogue, tle, tmp_path)
    truth = json.loads(result.truth_path.read_text())
    wcs = build_truth_wcs(scene)
    assert np.allclose(np.array(truth["wcs"]["cd"]), wcs.wcs.cd)
    assert np.allclose(truth["wcs"]["crval"], wcs.wcs.crval)
    assert np.allclose(truth["wcs"]["crpix"], wcs.wcs.crpix)


# ---------------------------------------------------------------------------
# AC 2.5 — streak geometry: independently recompute ISS pixels from skyfield and
# assert truth.json's endpoints/midpoint match (test MAY read truth).
# ---------------------------------------------------------------------------


def _propagate_iss_radec(scene, tle):
    """Independently propagate the ISS to exposure start/mid/end -> ICRS RA/Dec (deg)."""
    import datetime as dt

    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    sat = EarthSatellite(tle.line1, tle.line2, tle.name or "SAT", ts)
    obs = wgs84.latlon(
        scene.observer_lat_deg, scene.observer_lon_deg, elevation_m=scene.observer_elev_m
    )
    start = dt.datetime.fromisoformat(scene.utc.replace("Z", "+00:00"))
    out = {}
    for label, offset in (("start", 0.0), ("mid", scene.exposure_s / 2.0), ("end", scene.exposure_s)):
        t = ts.from_datetime(start + dt.timedelta(seconds=offset))
        ra, dec, _ = (sat - obs).at(t).radec()
        out[label] = (ra._degrees, dec.degrees)
    return out


def test_propagate_satellite_radec_pure_helper_matches_inline(scene, tle):
    """The extracted pure single-instant helper produces the SAME ICRS RA/Dec as the inline
    skyfield call render uses — proving the M1 Sprint-3 extraction is behavior-preserving and that
    real satellite-truth (ingest path) shares render's exact ICRS frame.
    """
    import datetime as dt

    from tracklet.render import propagate_satellite_radec

    start = dt.datetime.fromisoformat(scene.utc.replace("Z", "+00:00"))
    when = start + dt.timedelta(seconds=scene.exposure_s / 2.0)  # the exposure midpoint instant
    ra, dec = propagate_satellite_radec(
        tle,
        scene.observer_lat_deg,
        scene.observer_lon_deg,
        scene.observer_elev_m,
        when,
    )
    exp_ra, exp_dec = _propagate_iss_radec(scene, tle)["mid"]
    assert ra == pytest.approx(exp_ra, abs=1e-9)
    assert dec == pytest.approx(exp_dec, abs=1e-9)


def test_streak_radec_matches_independent_propagation(scene, catalogue, tle, tmp_path):
    result = render_scene(scene, catalogue, tle, tmp_path)
    truth = json.loads(result.truth_path.read_text())
    expected = _propagate_iss_radec(scene, tle)
    for key in ("start", "mid", "end"):
        ra, dec = expected[key]
        assert truth["satellite"][key]["ra_deg"] == pytest.approx(ra, abs=1e-7)
        assert truth["satellite"][key]["dec_deg"] == pytest.approx(dec, abs=1e-7)


def test_streak_pixels_match_propagated_geometry(scene, catalogue, tle, tmp_path):
    result = render_scene(scene, catalogue, tle, tmp_path)
    truth = json.loads(result.truth_path.read_text())
    expected = _propagate_iss_radec(scene, tle)
    wcs = build_truth_wcs(scene)
    for key in ("start", "mid", "end"):
        ra, dec = expected[key]
        ex, ey = wcs.wcs_world2pix(ra, dec, 0)
        gx, gy = truth["satellite_px"][key]
        assert gx == pytest.approx(float(ex), abs=1e-3)
        assert gy == pytest.approx(float(ey), abs=1e-3)


def test_streak_midpoint_is_frame_center(scene, catalogue, tle, tmp_path):
    # By construction the scene centers on the ISS at the exposure midpoint -> the streak midpoint
    # lands on the central pixel ((W-1)/2, (H-1)/2). Pins the truth-at-midpoint convention.
    result = render_scene(scene, catalogue, tle, tmp_path)
    truth = json.loads(result.truth_path.read_text())
    mx, my = truth["satellite_px"]["mid"]
    assert mx == pytest.approx((scene.width_px - 1) / 2.0, abs=1.0)
    assert my == pytest.approx((scene.height_px - 1) / 2.0, abs=1.0)


def test_streak_endpoints_in_frame(scene, catalogue, tle, tmp_path):
    # Sanity: the streak must actually fit inside the frame (else the scene is incoherent).
    result = render_scene(scene, catalogue, tle, tmp_path)
    truth = json.loads(result.truth_path.read_text())
    for key in ("start", "mid", "end"):
        x, y = truth["satellite_px"][key]
        assert 0 <= x <= scene.width_px - 1
        assert 0 <= y <= scene.height_px - 1


# ---------------------------------------------------------------------------
# Stars: a representative sanity check that bright stars actually land in-frame.
# ---------------------------------------------------------------------------


def test_bright_star_pixel_has_signal(scene, catalogue, tle, tmp_path):
    # The brightest in-frame Gaia star should leave a clear peak above the local background.
    result = render_scene(scene, catalogue, tle, tmp_path)
    wcs = build_truth_wcs(scene)
    ra = np.asarray(catalogue["ra"], dtype=float)
    dec = np.asarray(catalogue["dec"], dtype=float)
    mag = np.asarray(catalogue["phot_g_mean_mag"], dtype=float)
    x, y = wcs.wcs_world2pix(ra, dec, 0)
    in_frame = (x >= 2) & (x < scene.width_px - 2) & (y >= 2) & (y < scene.height_px - 2)
    assert in_frame.sum() > 100, "expected many stars projected in-frame"
    # brightest in-frame star
    idx = np.argmin(np.where(in_frame, mag, np.inf))
    px, py = int(round(float(x[idx]))), int(round(float(y[idx])))
    peak = result.image[py - 2 : py + 3, px - 2 : px + 3].max()
    median_bg = np.median(result.image)
    assert peak > median_bg + 5 * scene.read_noise_e
