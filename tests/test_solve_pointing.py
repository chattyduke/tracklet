"""S3 solve_pointing tests — blind plate-solve (ACs 3.1-3.3).

The seal in one sentence: ``solve_pointing(image_path, scale_hint)`` sees ONLY the delivered,
WCS-free ``image.fits`` and runs a BLIND ``solve-field`` (no ``--ra/--dec`` seed) — so even the
scene's known pointing is never fed in. The non-circularity guarantee is therefore structural
(AC 3.3: the signature has no truth path and the module imports no truth) AND empirical (AC 3.1:
a real blind solve on the golden streaked frame independently recovers a WCS that matches the
sealed truth WCS to a few arcsec).

AC 3.1 / 3.2 are ``@pytest.mark.solver`` — they shell out to the real ``solve-field`` against the
S0-installed 4100-series indexes and are EXCLUDED by ``pytest -m "not solver"``. AC 3.3 is a pure
structural check and stays in the default (non-solver) suite.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

from tracklet import solve_pointing as sp_module
from tracklet.solve_pointing import SolveFailure, SolveResult, solve_pointing
from tracklet.render import render_scene
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


# ---------------------------------------------------------------------------
# AC 3.3 (non-solver) — the structural non-circularity guarantee.
# solve_pointing's signature takes ONLY (image_path, scale_hint); the module references no truth.
# This runs in `pytest -m "not solver"` (no solve-field needed).
# ---------------------------------------------------------------------------


def test_signature_takes_only_image_and_scale_hint():
    params = list(inspect.signature(solve_pointing).parameters)
    # The contract signature is exactly (image_path, scale_hint) — no truth path, no wcs, no seed.
    assert params == ["image_path", "scale_hint"], params


def test_module_does_not_reference_truth():
    """AST/source scan: solve_pointing never imports the truth loader nor names truth.json.

    A blind solver that reached for the sealed truth would silently destroy the non-circularity
    argument. Catch it structurally rather than trusting the runtime path.
    """
    source = Path(sp_module.__file__).read_text()
    # No literal reference to the sealed-truth artifact or its loader.
    assert "truth.json" not in source
    assert "_load_truth" not in source

    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            imported += [f"{mod}.{alias.name}" for alias in node.names]
    # solve_pointing must not import scene/render/score (the truth-aware modules).
    for forbidden in ("score", "tracklet.score", "render", "tracklet.render", "scene", "tracklet.scene"):
        assert not any(name == forbidden or name.endswith("." + forbidden) for name in imported), (
            f"solve_pointing must not import {forbidden}: imports={imported}"
        )


# ---------------------------------------------------------------------------
# AC 3.1 (@solver) — the de-risk: a REAL blind solve on the golden STREAKED frame must
# converge and recover a WCS that matches the sealed TRUTH WCS to within tolerance.
#
# This is the empirical gate on the bright-streak watch-item: solve-field runs its own source
# extraction over the delivered composited frame (streak included — solving a star-only layer
# would be cheating). If the streak perturbs the solve, this test fails for real.
# ---------------------------------------------------------------------------

# solve-field's internal solve RMS on a real field is ~1-2"; we render a synthetic TAN field
# whose true WCS is exact, so the recovered-vs-true agreement at the frame center + corners is
# dominated by solve-field's own astrometric fit. 10" is a defensible ceiling — comfortably above
# the ~1-2" solver RMS yet far tighter than the ~half-degree that a wrong-asterism / off-by-a-tile
# solve would produce. (The S0 smoke recovered the center to 14.2" on a real-Gaia xylist; a clean
# synthetic field with exact truth should do at least as well at the center.)
_MATCH_TOL_ARCSEC = 10.0


@pytest.fixture(scope="module")
def golden(scene, tmp_path_factory):
    """Render the golden scene ONCE -> the delivered image.fits + the sealed truth.json.

    The image is the full composited frame WITH the streak (the clean-FITS seal means there is
    exactly one delivered frame). solve_pointing is given ONLY image.fits; the truth WCS is read
    here in the TEST (the solver-success test MAY read truth) to score the recovered WCS.
    """
    out = tmp_path_factory.mktemp("golden")
    catalogue = load_catalogue(default_catalogue_path(scene))
    tle = load_tle(default_tle_path(scene))
    result = render_scene(scene, catalogue, tle, out)
    return result


@pytest.mark.solver
def test_blind_solve_recovers_true_wcs_on_golden_streaked_frame(scene, golden):
    scale_hint = {"fov_deg": scene.fov_deg}
    result = solve_pointing(str(golden.image_path), scale_hint)

    assert isinstance(result, SolveResult), (
        f"blind solve did not converge on the golden streaked frame: {result!r}"
    )
    recovered = result.wcs
    true_wcs = golden.wcs

    # Project a grid of probe pixels (center + 4 corners + 4 edge-mids) through BOTH WCSs and
    # assert the recovered sky position agrees with the true sky position to within tolerance.
    h, w = scene.height_px, scene.width_px
    xs = np.array([w / 2, 0, w - 1, 0, w - 1, w / 2, w / 2, 0, w - 1], dtype=float)
    ys = np.array([h / 2, 0, 0, h - 1, h - 1, 0, h - 1, h / 2, h / 2], dtype=float)

    tr_ra, tr_dec = true_wcs.wcs_pix2world(xs, ys, 0)
    rc_ra, rc_dec = recovered.wcs_pix2world(xs, ys, 0)
    seps = SkyCoord(rc_ra * u.deg, rc_dec * u.deg).separation(
        SkyCoord(tr_ra * u.deg, tr_dec * u.deg)
    ).arcsec

    worst = float(np.max(seps))
    assert worst < _MATCH_TOL_ARCSEC, (
        f"recovered WCS disagrees with truth by {worst:.2f}\" (max over center+corners+edges); "
        f"tol {_MATCH_TOL_ARCSEC}\". per-probe arcsec: {np.round(seps, 2).tolist()}"
    )


# ---------------------------------------------------------------------------
# AC 3.2 (@solver) — honest failure: a pure-noise frame must RETURN a SolveFailure (not raise).
# ---------------------------------------------------------------------------


@pytest.mark.solver
def test_pure_noise_frame_returns_solvefailure_not_raise(scene, tmp_path):
    # A small pure-noise frame (no stars, no streak) — solve-field finds no matchable asterism
    # and fails to solve. Keep it small + a short timeout so the negative case is fast.
    rng = np.random.default_rng(12345)
    noise = rng.normal(200.0, 5.0, size=(512, 512)).astype(np.float32)
    image_path = tmp_path / "noise.fits"
    fits.PrimaryHDU(data=noise).writeto(image_path, overwrite=True)

    scale_hint = {"fov_deg": scene.fov_deg}
    result = solve_pointing(str(image_path), scale_hint)

    assert isinstance(result, SolveFailure), (
        f"pure-noise frame must RETURN a SolveFailure, got {result!r}"
    )
    assert result.reason, "SolveFailure must carry a non-empty reason string"


# ---------------------------------------------------------------------------
# S6 carried-fix (NON-solver) — a MALFORMED scale_hint must RETURN a typed SolveFailure, not raise.
#
# _scale_bounds previously raised KeyError on a dict missing fov_deg/low/high (and ValueError /
# TypeError on a non-numeric hint), so a caller-side mistake surfaced as a stack trace rather than
# the contract's honest typed failure. The fix validates the hint up front and returns a
# SolveFailure whose reason names the bad hint — deterministic and solver-independent (it must NOT
# need solve-field on PATH), so this runs under `pytest -m "not solver"`.
# ---------------------------------------------------------------------------


def test_malformed_scale_hint_dict_returns_solvefailure_not_raise():
    """A dict missing fov_deg / low / high -> typed SolveFailure (NOT a KeyError stack trace)."""
    result = solve_pointing("anything.fits", {"bad_key": 1})
    assert isinstance(result, SolveFailure), (
        f"malformed scale_hint must RETURN a SolveFailure, got {result!r}"
    )
    assert result.reason, "SolveFailure must carry a non-empty reason string"
    assert "hint" in result.reason.lower(), (
        f"reason should name the bad scale hint, got {result.reason!r}"
    )


def test_non_numeric_scale_hint_returns_solvefailure_not_raise():
    """A non-numeric hint (un-floatable) -> typed SolveFailure, never raised."""
    result = solve_pointing("anything.fits", "not-a-number")
    assert isinstance(result, SolveFailure), (
        f"non-numeric scale_hint must RETURN a SolveFailure, got {result!r}"
    )
    assert "hint" in result.reason.lower(), (
        f"reason should name the bad scale hint, got {result.reason!r}"
    )


def test_non_numeric_fov_deg_value_returns_solvefailure_not_raise():
    """A dict with a non-numeric fov_deg value -> typed SolveFailure, never raised."""
    result = solve_pointing("anything.fits", {"fov_deg": "wide"})
    assert isinstance(result, SolveFailure), (
        f"non-numeric fov_deg must RETURN a SolveFailure, got {result!r}"
    )
    assert "hint" in result.reason.lower(), result.reason
