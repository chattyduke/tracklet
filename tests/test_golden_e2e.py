"""S7 golden end-to-end test — the executable Definition of Done (@solver, AC 7.2).

THIS test IS the milestone gate. It renders the frozen synthetic-from-real-data scene, runs the
FULL BLIND pipeline exactly as ``make run`` does — blind plate-solve (no position seed) -> streak
detect -> lift the midpoint through the RECOVERED (never the true) WCS -> score against the sealed
truth — and asserts the on-sky residual is under the published threshold. The actual residual is
ALWAYS reported (pass or fail) alongside the expected ~2-4" error budget, the <5" stretch target,
and the 10" gate.

Non-circularity: solve_pointing is given ONLY the WCS-free image.fits and gets NO --ra/--dec seed;
measure_position uses the RECOVERED WCS; score is the only reader of the sealed truth. So the
residual is a genuine, non-circular measurement (the seal is formally pinned in tests/test_seal.py).

On the pixel convention: the 10" gate is DELIBERATELY loose (~2-3x the error budget) so a stranger's
legitimate blind solve cannot flake — see the plan's portability rationale and score.py's
RESIDUAL_THRESHOLD_ARCSEC note. A 1-px convention error (CD-sign / Y-flip / 0-vs-1 origin) would push
the residual to ~7" — still under 10" — so this gate is NOT the guard against a convention
regression. That class is pinned INDEPENDENTLY and DETERMINISTICALLY (no solver, sub-pixel) by the
round-trip WCS tests that run on every ``pytest -m "not solver"``:
test_render.py::test_wcs_round_trip_subpixel_grid (<1e-6 px),
test_render.py::test_wcs_{ra_increases_left,dec_increases_up,center_maps_to_central_pixel}, and
test_measure_position.py::test_measure_round_trips_pixel_through_world_and_back (<1e-3 px). A 1-px
regression fails those by ~1e3-1e6x their tolerance — so a convention bug cannot hide under this gate.
The <5" stretch target is reported every run so any drift toward that regime is immediately visible.

@solver: needs solve-field + the 4100-series indexes (the S0 gate). Run via ``make test-golden``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from astropy.coordinates import SkyCoord

from tracklet.detect_streak import StreakDetection, detect_streak
from tracklet.measure_position import measure_position
from tracklet.render import render_scene
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)
from tracklet.score import RESIDUAL_THRESHOLD_ARCSEC, score
from tracklet.solve_pointing import SolveResult, solve_pointing

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"

# Documented error budget (quadrature): transverse centroid ~2" (+) solve-field WCS RMS ~1-2" (+)
# TAN projection/discretization <1" -> expected ~2-4". The <5" stretch target flags a gross
# regression early; the 10" gate (score.RESIDUAL_THRESHOLD_ARCSEC) is the portable DoD pass criterion.
_EXPECTED_BAND_ARCSEC = (2.0, 4.0)
_STRETCH_TARGET_ARCSEC = 5.0


@pytest.mark.solver
def test_golden_e2e_blind_solve_residual_under_threshold(tmp_path, capsys):
    scene = build_scene(str(_CONFIG))
    catalogue = load_catalogue(default_catalogue_path(scene))
    tle = load_tle(default_tle_path(scene))

    # 1) Render the frozen scene -> WCS-free image.fits + sealed truth.json (render is sole writer).
    rendered = render_scene(scene, catalogue, tle, tmp_path / "out")

    # 2) BLIND plate-solve the delivered image (scale-only hint -> independent pointing recovery).
    solve = solve_pointing(str(rendered.image_path), {"fov_deg": scene.fov_deg})
    assert isinstance(solve, SolveResult), (
        f"blind solve must converge on the golden frame; got {solve!r}"
    )

    # 3) Detect the streak from the SAME WCS-free image.
    detection = detect_streak(str(rendered.image_path))
    assert isinstance(detection, StreakDetection), (
        f"streak detection must succeed on the golden frame; got {detection!r}"
    )

    # 4) Lift the midpoint through the RECOVERED WCS (never the true WCS); 5) score vs sealed truth.
    measured = measure_position(detection, solve.wcs)
    assert isinstance(measured, SkyCoord)
    result = score(measured, str(rendered.truth_path))

    # ALWAYS surface the real number + budget + targets, pass OR fail. capsys.disabled() bypasses
    # pytest capture so the headline shows on success AND failure, even under `-q` (make test-golden).
    headline = (
        f"[AC 7.2] GOLDEN E2E BLIND-SOLVE RESIDUAL = {result.residual_arcsec:.3f}\" "
        f"(expected ~{_EXPECTED_BAND_ARCSEC[0]:.0f}-{_EXPECTED_BAND_ARCSEC[1]:.0f}\", "
        f"stretch <{_STRETCH_TARGET_ARCSEC:.0f}\", gate {RESIDUAL_THRESHOLD_ARCSEC:.0f}\") "
        f"-> {'PASS' if result.passed else 'FAIL'}"
    )
    with capsys.disabled():
        print("\n" + headline)

    # THE DoD GATE: the residual is under the published portable threshold (AC 7.2 / M0 DoD).
    assert result.residual_arcsec < RESIDUAL_THRESHOLD_ARCSEC, (
        f"golden residual exceeds the DoD gate {RESIDUAL_THRESHOLD_ARCSEC}\" — M0 not met. {headline}"
    )
    # A genuine recovery has a non-zero residual; an exact 0 would smell of a truth leak, not a solve.
    assert result.residual_arcsec > 0.0, "a real independent recovery has a non-zero residual"
