"""M1 Sprint 4 / AC 4.1 + AC 2.5 — the REAL-image end-to-end @solver gate (skip-if-frame-missing).

These tests exercise the genuine telescope frame: ingest -> blind solve -> detect (AC 2.5, the binding
Sprint-1 confirmation that the NORMALIZED image still solves+detects) and the full run.py --image/--meta
path (AC 4.1). They are @solver (need solve-field + indexes) AND need the real frame on disk; the frame
is gitignored (*.fits) and fetched on demand via tests/fixtures/real/fetch.sh, so a missing frame is a
SKIP, not a failure (a skip is NOT a frame rejection).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

_REAL = Path(__file__).resolve().parent / "fixtures" / "real"
_FRAME = _REAL / "20221118T024706C1o.fits"
_META = _REAL / "meta.toml"

_frame_missing = not _FRAME.exists()
_skip_reason = (
    f"real frame {_FRAME.name} not on disk — run tests/fixtures/real/fetch.sh (gitignored *.fits)"
)


@pytest.mark.solver
@pytest.mark.skipif(_frame_missing, reason=_skip_reason)
def test_ac25_normalized_real_image_blind_solves_and_detects():
    """AC 2.5 (BINDING Sprint-1 confirmation): the NORMALIZED, WCS-stripped ingested real image still
    blind-solves AND detects — proving the ingest normalization preserved the solvable content."""
    import tempfile

    from tracklet.detect_streak import DetectFailure, detect_streak
    from tracklet.ingest import ingest_external_image
    from tracklet.solve_pointing import SolveFailure, solve_pointing

    meta = tomllib.loads(_META.read_text())
    with tempfile.TemporaryDirectory() as td:
        res = ingest_external_image(str(_FRAME), meta, td)
        solve = solve_pointing(str(res.image_path), {"fov_deg": meta["solver"]["fov_deg"]})
        assert not isinstance(solve, SolveFailure), (
            f"the normalized real image must blind-solve; got SolveFailure: "
            f"{getattr(solve, 'reason', '')}"
        )
        det = detect_streak(str(res.image_path))
        assert not isinstance(det, DetectFailure), (
            f"the normalized real image must detect the trail; got DetectFailure: "
            f"{getattr(det, 'reason', '')}"
        )
        print(
            f"\n[AC 2.5] normalized real image BLIND-SOLVES + DETECTS: trail "
            f"{det.length_px:.0f} px @ {det.angle_deg:.2f} deg"
        )


@pytest.mark.solver
@pytest.mark.skipif(_frame_missing, reason=_skip_reason)
def test_ac41_real_image_run_produces_numeric_residual_passing_plausibility(tmp_path, capsys):
    """AC 4.1 + AC 6.1: run.py --image/--meta on the locked frame produces a NUMERIC residual that
    PASSES the AC-4.6 plausibility gate (recovered field overlaps the expected pointing field).

    The NON-CIRCULAR C1 camera offset is committed in meta (camera_offset_ra/dec_deg, derived in
    tick 25 by blind-solving 3 OTHER same-night C1 frames — 024735/024757/024816 — and taking
    mean(recovered - commanded), scatter 0.0001 deg). With it the expected pointing center =
    commanded + offset = (305.5563, -14.9639), which the target frame's own blind-recovered center
    (305.5565, -14.9640) overlaps to 0.0002 deg << the 1.705 deg half-field tolerance — so the gate
    confirms field overlap and the run emits the milestone numeric residual (~315.5", dominated by the
    documented 0.598-day TLE-age along-track term — an honest real-frame number, NOT a synthetic gate pass).
    """
    import math

    from tracklet.run import main

    out = tmp_path / "out"
    rc = main(["--image", str(_FRAME), "--meta", str(_META), "--out", str(out)])
    captured = capsys.readouterr()
    assert rc == 0, (
        f"real-image run must exit 0 with a plausibility-passing residual; got rc={rc}.\n"
        f"stdout:\n{captured.out}"
    )
    residual_txt = out / "residual.txt"
    assert residual_txt.exists(), "a passing real run must write residual.txt"
    residual = float(residual_txt.read_text().strip())
    assert math.isfinite(residual), f"residual must be finite; got {residual!r}"
    print(f"\n[AC 4.1] REAL-IMAGE BLIND-SOLVE RESIDUAL = {residual:.4f}\"")
    assert (out / "report.md").exists(), "a passing real run must write a report"
