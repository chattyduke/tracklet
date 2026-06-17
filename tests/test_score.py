"""S5 score tests — AC 5.2 (arcsec arithmetic) + AC 5.3 (golden frame, TRUE WCS) + the truth-read
seal. All NON-solver.

score(measured, truth_path) -> ScoreResult is the END of the pipeline: it reads the SEALED truth's
``scored_truth`` RA/Dec (the satellite position at the exposure MIDPOINT) and reports the on-sky
arcsecond separation between the measured and true positions. ``score._load_truth`` is the SOLE
truth reader in the whole repo besides render (the writer) — every other module is structurally
sealed away from truth.json.

AC 5.3 isolates detect+measure error by using the TRUE WCS ``build_truth_wcs(scene)`` (NOT a blind
solve) — the full blind-solve residual is S7's @solver e2e, out of scope here. No solve-field, no
network, no @solver: this whole file runs under ``pytest -m "not solver"``.
"""
from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u

from tracklet import score as score_module
from tracklet.score import RESIDUAL_THRESHOLD_ARCSEC, ScoreResult, score
from tracklet.measure_position import measure_position
from tracklet.detect_streak import detect_streak, StreakDetection
from tracklet.render import build_truth_wcs, render_scene
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


@pytest.fixture(scope="module")
def catalogue(scene):
    return load_catalogue(default_catalogue_path(scene))


@pytest.fixture(scope="module")
def tle(scene):
    return load_tle(default_tle_path(scene))


@pytest.fixture(scope="module")
def golden(scene, catalogue, tle, tmp_path_factory):
    """Render the golden scene ONCE -> delivered image.fits + sealed truth.json (same idiom as
    test_render.py / test_solve_pointing.py / test_detect_streak.py)."""
    out = tmp_path_factory.mktemp("golden_score")
    return render_scene(scene, catalogue, tle, out)


def _write_truth(tmp_path, ra_deg: float, dec_deg: float) -> Path:
    """Write a minimal truth.json whose scored_truth is a KNOWN RA/Dec (the only key score reads)."""
    truth = {"scored_truth": {"ra_deg": ra_deg, "dec_deg": dec_deg}}
    path = tmp_path / "truth.json"
    path.write_text(json.dumps(truth))
    return path


# ---------------------------------------------------------------------------
# AC 5.2 — arcsec arithmetic vs a HAND-COMPUTED separation, + the passed flag, + the scored_truth key.
# ---------------------------------------------------------------------------


def test_residual_matches_hand_computed_dec_offset(tmp_path):
    """A pure-Dec offset of 0.001 deg == 3.6" exactly; score must report 3.6" (tight tol) and pass."""
    truth_ra, truth_dec = 83.5, -5.0
    truth_path = _write_truth(tmp_path, truth_ra, truth_dec)

    # Measured is the truth shifted purely in Dec by 0.001 deg = 3.6 arcsec (a meridian arc, so the
    # great-circle separation equals the Dec delta exactly — independent of RA/cos(dec)).
    measured = SkyCoord((truth_ra) * u.deg, (truth_dec + 0.001) * u.deg, frame="icrs")

    result = score(measured, str(truth_path))
    assert isinstance(result, ScoreResult), f"expected ScoreResult, got {type(result)!r}"
    assert result.residual_arcsec == pytest.approx(3.6, abs=1e-4), result.residual_arcsec
    assert result.threshold_arcsec == RESIDUAL_THRESHOLD_ARCSEC
    assert result.passed is True  # 3.6" < 10" threshold


def test_residual_matches_hand_computed_when_far(tmp_path):
    """A 20" pure-Dec offset must report ~20" and FAIL the < threshold gate (honest, never clamped)."""
    truth_ra, truth_dec = 200.0, 30.0
    truth_path = _write_truth(tmp_path, truth_ra, truth_dec)

    # 20 arcsec = 20/3600 deg in pure Dec.
    measured = SkyCoord(truth_ra * u.deg, (truth_dec + 20.0 / 3600.0) * u.deg, frame="icrs")

    result = score(measured, str(truth_path))
    assert result.residual_arcsec == pytest.approx(20.0, abs=1e-3), result.residual_arcsec
    assert result.passed is False  # 20" > 10" threshold


def test_load_truth_reads_scored_truth_key(tmp_path):
    """score._load_truth returns the scored_truth RA/Dec as an ICRS SkyCoord (the sole truth read)."""
    truth_path = _write_truth(tmp_path, 12.34, 56.78)
    coord = score_module._load_truth(str(truth_path))
    assert isinstance(coord, SkyCoord)
    assert coord.icrs.ra.deg == pytest.approx(12.34)
    assert coord.icrs.dec.deg == pytest.approx(56.78)


def test_score_result_is_frozen(tmp_path):
    """ScoreResult is a frozen dataclass — the scored record is immutable once computed."""
    truth_path = _write_truth(tmp_path, 10.0, 10.0)
    result = score(SkyCoord(10.0 * u.deg, 10.0 * u.deg, frame="icrs"), str(truth_path))
    with pytest.raises(Exception):
        result.residual_arcsec = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC 5.3 — golden frame, TRUE WCS: isolates detect+measure error end-to-end (NON-solver).
# render -> detect_streak -> measure_position(true WCS) -> score; residual must be < threshold.
# ---------------------------------------------------------------------------


def test_golden_frame_residual_under_threshold_with_true_wcs(scene, golden):
    """End-to-end on the golden frame using the TRUE WCS (NO solve-field): residual < threshold.

    This isolates the detect + measure error (the blind-solve contribution is S7's @solver e2e).
    Prints the actual arcsec residual (expect ~1-2") so the threshold can be judged against reality.
    """
    detection = detect_streak(str(golden.image_path))
    assert isinstance(detection, StreakDetection), f"expected a StreakDetection, got {detection!r}"

    wcs = build_truth_wcs(scene)
    measured = measure_position(detection, wcs)
    result = score(measured, str(golden.truth_path))

    print(f"\n[AC 5.3] golden-frame residual (TRUE WCS) = {result.residual_arcsec:.4f}\" "
          f"(threshold {RESIDUAL_THRESHOLD_ARCSEC}\")")
    assert result.residual_arcsec < RESIDUAL_THRESHOLD_ARCSEC, (
        f"detect+measure residual {result.residual_arcsec:.4f}\" exceeds "
        f"threshold {RESIDUAL_THRESHOLD_ARCSEC}\""
    )
    assert result.passed is True


# ---------------------------------------------------------------------------
# The score-side seal — score is the module doing the truth read; _load_truth exists and is the
# canonical loader. (measure_position's reciprocal seal lives in test_measure_position.py.)
# ---------------------------------------------------------------------------


def test_score_signature_is_measured_and_truth_path():
    params = list(inspect.signature(score).parameters)
    assert params == ["measured", "truth_path"], params


def test_load_truth_is_the_truth_reader():
    """score defines _load_truth and names truth's key — it IS the sole truth-aware leaf module."""
    source = Path(score_module.__file__).read_text()
    tree = ast.parse(source)
    funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "_load_truth" in funcs, "score must define the canonical _load_truth loader"
    assert "scored_truth" in source, "score._load_truth must read the scored_truth key"
