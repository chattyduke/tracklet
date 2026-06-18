"""M1 Sprint 4 — run.py real-image entry point (--image/--meta) tests (ACs 4.2-4.6 + seal).

The non-frame-dependent ACs are pinned here (non-solver): the synthetic default path is unchanged
(4.2), real-frame solve/detect failures are honest with no fabricated residual (4.3), the solver is
fed a WCS-free image + scale-only hint (4.4), the measurement uses the blind-recovered WCS (4.5), and
a wrong-field lock is rejected by the AC-4.6 plausibility gate as a TYPED failure (4.6). The full real
@solver e2e (AC 4.1) lives in tests/test_real_image_e2e.py (skip-if-frame-missing).
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from tracklet import run as run_module
from tracklet.run import main
from tracklet.detect_streak import DetectFailure
from tracklet.solve_pointing import SolveFailure, SolveResult

_REPO = Path(__file__).resolve().parent.parent
_REAL = _REPO / "tests" / "fixtures" / "real"
_META = _REAL / "meta.toml"


def _fake_clean_fits(path: Path, shape=(64, 64)):
    """Write a tiny WCS-free FITS for tests that monkeypatch the solver/detector."""
    fits.PrimaryHDU(np.zeros(shape, dtype=np.float32)).writeto(path, overwrite=True)


def _tan_wcs(center_ra, center_dec, naxis1, naxis2, scale_deg):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crpix = [(naxis1 + 1) / 2.0, (naxis2 + 1) / 2.0]
    w.wcs.crval = [center_ra, center_dec]
    w.wcs.cdelt = [-scale_deg, scale_deg]
    return w


# ---------------------------------------------------------------------------
# AC 4.2 — the synthetic default path is UNCHANGED (no --image/--meta given).
# ---------------------------------------------------------------------------


def test_synthetic_default_path_still_parses_and_runs_failure_branch(tmp_path, capsys, monkeypatch):
    """With NO --image/--meta, run still takes the synthetic path. We monkeypatch solve to a typed
    failure so this stays non-solver, proving the default branch + honest-failure contract intact."""
    monkeypatch.setattr(
        run_module, "solve_pointing", lambda image_path, scale_hint: SolveFailure(reason="x")
    )
    rc = main(["--out", str(tmp_path / "out")])
    assert rc == 2  # synthetic path's honest solve-failure exit code, unchanged
    assert "could not solve" in capsys.readouterr().out.lower()


# ---------------------------------------------------------------------------
# AC 4.3 — real-frame solve/detect failures are HONEST: exit 2/3, labelled, no residual.txt.
# ---------------------------------------------------------------------------


def test_real_path_solve_failure_is_honest_no_residual(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"

    # ingest -> a tiny clean image; solve -> typed failure. No frame needed (ingest is monkeypatched).
    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        _fake_clean_fits(p)
        return IngestResult(image=np.zeros((64, 64), np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))
    monkeypatch.setattr(
        run_module, "solve_pointing", lambda image_path, scale_hint: SolveFailure(reason="no asterism")
    )

    rc = main(["--image", "ignored.fits", "--meta", str(_META), "--out", str(out)])
    captured = capsys.readouterr()
    assert rc == 2, "a real-path SolveFailure must exit 2"
    assert "could not solve" in captured.out.lower()
    assert "no asterism" in captured.out
    assert not (out / "residual.txt").exists(), "no fabricated residual on a solve failure"


def test_real_path_detect_failure_is_honest_no_residual(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"

    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        _fake_clean_fits(p)
        return IngestResult(image=np.zeros((64, 64), np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))
    monkeypatch.setattr(
        run_module, "solve_pointing",
        lambda image_path, scale_hint: SolveResult(
            wcs=_tan_wcs(305.5565, -14.964, 64, 64, 2 / 3600), solve_seconds=0.0
        ),
    )
    monkeypatch.setattr(
        run_module, "detect_streak", lambda image_path: DetectFailure(reason="no linear features")
    )

    rc = main(["--image", "ignored.fits", "--meta", str(_META), "--out", str(out)])
    captured = capsys.readouterr()
    assert rc == 3, "a real-path DetectFailure must exit 3"
    assert "could not detect" in captured.out.lower()
    assert not (out / "residual.txt").exists(), "no fabricated residual on a detect failure"


# ---------------------------------------------------------------------------
# AC 4.6 — a WRONG-FIELD LOCK (recovered field does NOT overlap expected) is an HONEST typed failure,
# NOT a flattering residual. We feed a recovered WCS far from the expected pointing center.
# ---------------------------------------------------------------------------


def test_real_path_wrong_field_lock_is_typed_failure_not_residual(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"

    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        _fake_clean_fits(p, shape=(6220, 6144))
        return IngestResult(image=np.zeros((6220, 6144), np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))
    # A WCS 10+ deg away from BOTH commanded and the true field -> wrong-field lock.
    monkeypatch.setattr(
        run_module, "solve_pointing",
        lambda image_path, scale_hint: SolveResult(
            wcs=_tan_wcs(290.0, 0.0, 6144, 6220, 2 / 3600), solve_seconds=0.0
        ),
    )
    # detect succeeds, but the gate must fire BEFORE a residual is trusted.
    from tracklet.detect_streak import StreakDetection
    monkeypatch.setattr(
        run_module, "detect_streak",
        lambda image_path: StreakDetection(
            endpoints=((100.0, 100.0), (200.0, 200.0)), midpoint=(150.0, 150.0),
            angle_deg=45.0, length_px=141.0,
        )
    )

    rc = main(["--image", "ignored.fits", "--meta", str(_META), "--out", str(out)])
    captured = capsys.readouterr()
    assert rc != 0, "a wrong-field lock must be a non-zero typed failure"
    assert "wrong field" in captured.out.lower() or "plausib" in captured.out.lower() or \
        "does not overlap" in captured.out.lower(), captured.out
    assert not (out / "residual.txt").exists(), (
        "a wrong-field lock must NOT write a flattering residual"
    )


# ---------------------------------------------------------------------------
# AC 4.4 / 4.5 / seal — structural: run feeds the solver a scale-only hint (no position prior) and
# measures through the BLIND-RECOVERED WCS; run never opens truth (score is sole reader).
# ---------------------------------------------------------------------------


def test_run_real_branch_solver_call_has_no_position_prior():
    """AC 4.4 — in run.py source, solve_pointing is called with a fov_deg scale hint ONLY; no
    --ra/--dec/--radius position seed and no header WCS is passed into the solver."""
    source = Path(run_module.__file__).read_text()
    tree = ast.parse(source)
    solve_calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "solve_pointing"
    ]
    assert solve_calls, "expected solve_pointing call(s) in run.py"
    for call in solve_calls:
        seg = ast.get_source_segment(source, call) or ""
        low = seg.lower()
        # blind: only a scale hint may be passed; no ra/dec/header-wcs seed.
        assert "fov_deg" in seg, seg
        assert "header" not in low and "crval" not in low and "--ra" not in low, seg


def test_run_still_never_opens_truth_with_real_branch():
    """The seal extends to the real branch: run.py still never names/opens truth, never json.load,
    never _load_truth (score remains the sole reader). assemble_real_truth returns a PATH object."""
    source = Path(run_module.__file__).read_text()
    assert "json.load" not in source
    assert "_load_truth" not in source
    assert "truth.json" not in source, "run.py must not name the sealed-truth artifact literally"


def _stub_truth(out_dir):
    """A RealTruthResult-shaped stub whose truth_path points at a real on-disk truth.json that
    score can read (so the success path is exercisable without the real frame)."""
    import json

    from tracklet.realtruth import RealTruthResult

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tp = out / "truth.json"
    tp.write_text(json.dumps({"scored_truth": {"ra_deg": 305.5565, "dec_deg": -14.964}}))
    return RealTruthResult(
        truth_path=tp, scored_truth_ra_deg=305.5565, scored_truth_dec_deg=-14.964,
        exposure_mid_utc=None, pointing_wcs=None, norad_id=53807,
    )
