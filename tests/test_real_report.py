"""M1 Sprint 5 — honest five-source degradation report tests (ACs 5.1-5.4).

The real-frame report must (5.1) always print the actual ``residual_arcsec`` verbatim — never
rounded-to-flatter, never fabricated; (5.2) name all FIVE degradation source classes; (5.3) on a typed
solve/detect/wrong-field failure, contain NO residual figure; (5.4) carry a pointing-vs-timing
decomposition computed from IN-MEMORY objects (the recovered satellite sky position vs the sealed
truth SkyCoord on the ScoreResult) with NO ``json.load`` outside ``score.py``.

The degradation section is rendered by the pure ``report.render_degradation_report`` helper (the plan's
home for the section); ``run.py::_write_real_report`` calls it on the success path. These tests pin the
pure renderer (no frame, no network) + the typed-failure no-residual contract through ``run.main``.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from tracklet import run as run_module
from tracklet.report import DegradationInputs, render_degradation_report
from tracklet.run import main
from tracklet.detect_streak import DetectFailure, StreakDetection
from tracklet.score import ScoreResult
from tracklet.solve_pointing import SolveFailure, SolveResult

_REPO = Path(__file__).resolve().parent.parent
_REAL = _REPO / "tests" / "fixtures" / "real"
_META = _REAL / "meta.toml"

# The five degradation source classes the report MUST name (AC 5.2). The matcher is keyword-based so
# the prose can read naturally; each tuple is a set of acceptable substrings for one source class.
_FIVE_SOURCE_KEYWORDS = [
    ("timing", "tle-age", "along-track", "exposure-midpoint", "exposure midpoint"),  # dominant
    ("atmosphere", "seeing", "refraction"),
    ("psf", "optics", "aberration"),
    ("plate scale", "plate-scale", "distortion"),
    ("detector noise", "read noise", "shot noise", "detector"),
]


def _score_result(measured_ra, measured_dec, truth_ra, truth_dec, threshold=10.0):
    """Build a real ScoreResult from two sky positions (the real separation, no fabrication)."""
    measured = SkyCoord(measured_ra, measured_dec, unit="deg", frame="icrs")
    truth = SkyCoord(truth_ra, truth_dec, unit="deg", frame="icrs")
    residual = float(measured.separation(truth).arcsec)
    return ScoreResult(
        residual_arcsec=residual, measured=measured, truth=truth,
        threshold_arcsec=threshold, passed=residual < threshold,
    )


def _degradation_inputs():
    """In-memory inputs for the pure degradation renderer — mirrors the real BW3 frame numbers."""
    # Recovered satellite position (measured) vs the sealed TLE truth at the exposure midpoint.
    # ~315" separation, dominated by along-track timing/TLE-age slip (the BW3 reality).
    result = _score_result(306.4830, -14.9660, 306.5250, -14.8890)
    detection = StreakDetection(
        endpoints=((100.0, 100.0), (5000.0, 5050.0)), midpoint=(4681.71, 3129.02),
        angle_deg=126.16, length_px=4956.0,
    )
    return DegradationInputs(
        score=result,
        detection=detection,
        tle_age_days=0.598,
        exposure_s=10.0,
        norad_id=53807,
        satellite_name="BLUEWALKER 3",
        pointing_truth=None,  # DDOTI carries no header WCS -> no pointing-vs-timing from a header WCS
    )


# ---------------------------------------------------------------------------
# AC 5.1 — the report contains the real residual_arcsec verbatim (no rounding-to-flatter).
# ---------------------------------------------------------------------------


def test_ac51_report_contains_real_residual_verbatim():
    di = _degradation_inputs()
    md = render_degradation_report(di)
    # The exact 4-dp residual must appear verbatim (the headline number is the data's, not flattered).
    assert f"{di.score.residual_arcsec:.4f}" in md, md


def test_ac51_residual_is_not_flattened_to_pass():
    di = _degradation_inputs()
    md = render_degradation_report(di)
    # An honest large residual must NOT be presented as a pass/under-threshold.
    assert di.score.residual_arcsec > di.score.threshold_arcsec  # this frame is honestly over gate
    assert "FAIL" in md, md  # the verdict is honest, not flattered to PASS


# ---------------------------------------------------------------------------
# AC 5.2 — the report names all FIVE degradation source classes, TLE-age along-track leading.
# ---------------------------------------------------------------------------


def _numbered_source_lines(md: str) -> "list[str]":
    """The structural degradation list: the lines of the form ``N. **<source>** — ...`` (lowercased).

    Pinning the numbered+bolded list (not incidental prose) is what makes AC 5.2 actually bite — if a
    source class is dropped, its numbered header disappears and the keyword is no longer on ANY list
    line, even if the word survives in a different source's description.
    """
    out = []
    for raw in md.splitlines():
        line = raw.strip()
        if len(line) >= 2 and line[0].isdigit() and line[1] == "." and "**" in line:
            out.append(line.lower())
    return out


def test_ac52_report_names_all_five_degradation_sources():
    di = _degradation_inputs()
    lines = _numbered_source_lines(render_degradation_report(di))
    assert len(lines) == 5, f"expected exactly five numbered degradation sources, got {len(lines)}"
    # Each of the five numbered list lines must carry its source class's keyword — so dropping a
    # class's NAME (not just an incidental mention elsewhere) flips this test red.
    for i, keyword_set in enumerate(_FIVE_SOURCE_KEYWORDS):
        assert any(k in lines[i] for k in keyword_set), (
            f"numbered source #{i + 1} ({lines[i]!r}) is missing a keyword from {keyword_set}"
        )


def test_ac52_tle_age_along_track_is_named_dominant():
    di = _degradation_inputs()
    md = render_degradation_report(di)
    low = md.lower()
    lines = _numbered_source_lines(md)
    # The FIRST numbered source (the structural "largest first") must be the TLE-age along-track term
    # AND carry the explicit (DOMINANT) structural flag — not buried as one of five equals.
    assert "along-track" in lines[0] or "along track" in lines[0], "source #1 must be the along-track term"
    assert "(dominant)" in lines[0], "source #1 must carry the explicit (DOMINANT) flag"
    # The narrative must also call it the dominant/leading term AND report the actual TLE age.
    assert "dominant / leading term" in low or "dominant/leading term" in low, (
        "the narrative must flag the along-track term as dominant/leading"
    )
    assert "0.598" in low, "the actual TLE age (0.598 d) must be reported verbatim"


# ---------------------------------------------------------------------------
# AC 5.4 — pointing-vs-timing decomposition from IN-MEMORY objects (no json.load outside score.py).
# ---------------------------------------------------------------------------


def test_ac54_decomposition_present_from_in_memory_objects():
    di = _degradation_inputs()
    md = render_degradation_report(di)
    low = md.lower()
    # The pointing-vs-timing decomposition is a STRUCTURAL section with its own heading (so removing
    # the section, not just an incidental word, flips this test red).
    assert "## pointing-vs-timing decomposition" in low, "the decomposition section heading must be present"
    # It must report the measured AND truth positions AND the displacement split — all derived from the
    # in-memory measured/truth SkyCoords. The actual measured RA (306.4826 deg) must appear verbatim.
    assert "measured satellite position" in low and "sealed truth" in low
    assert f"{di.score.measured.icrs.ra.deg:.6f}" in md, "measured RA must be reported from in-memory coord"
    assert f"{di.score.truth.icrs.ra.deg:.6f}" in md, "truth RA must be reported from in-memory coord"
    # The displacement decomposition (total + dRA/dDec) must be present, attributed along-track vs
    # cross-track/pointing.
    assert "displacement" in low and "along-track" in low
    assert "cross-track" in low or "pointing" in low


def test_ac54_renderer_uses_no_json_load():
    """The pure degradation renderer reads truth ONLY via the in-memory ScoreResult — never json.load
    and never _load_truth (score remains the sole deserializer; the renderer is downstream of score)."""
    import tracklet.report as report_module

    source = Path(report_module.__file__).read_text()
    tree = ast.parse(source)
    # No json.load / json.loads attribute call anywhere in report.py.
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("load", "loads"):
            base = node.value
            assert not (isinstance(base, ast.Name) and base.id == "json"), (
                "report.py must not call json.load/json.loads — truth is in-memory via ScoreResult"
            )
    assert "_load_truth" not in source, "report.py must not reach the score module's private loader"


# ---------------------------------------------------------------------------
# AC 5.3 — on a typed failure the report states the reason and contains NO residual figure.
# We exercise the real failure paths through run.main (solve / detect / wrong-field) and assert
# neither residual.txt nor any residual number is written.
# ---------------------------------------------------------------------------


def _fake_clean_fits(path: Path, shape=(64, 64)):
    fits.PrimaryHDU(np.zeros(shape, dtype=np.float32)).writeto(path, overwrite=True)


def _tan_wcs(center_ra, center_dec, naxis1, naxis2, scale_deg):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crpix = [(naxis1 + 1) / 2.0, (naxis2 + 1) / 2.0]
    w.wcs.crval = [center_ra, center_dec]
    w.wcs.cdelt = [-scale_deg, scale_deg]
    return w


def _stub_truth(out_dir):
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


def _patch_ingest(monkeypatch, out, shape=(64, 64)):
    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        _fake_clean_fits(p, shape)
        return IngestResult(image=np.zeros(shape, np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))


def test_ac53_solve_failure_report_has_no_residual(tmp_path, monkeypatch):
    out = tmp_path / "out"
    _patch_ingest(monkeypatch, out)
    monkeypatch.setattr(
        run_module, "solve_pointing", lambda image_path, scale_hint: SolveFailure(reason="no asterism")
    )
    rc = main(["--image", "x.fits", "--meta", str(_META), "--out", str(out)])
    assert rc == 2
    assert not (out / "residual.txt").exists()
    # No report.md, or if one exists it must contain NO residual figure (no "Residual:" line).
    report = out / "report.md"
    if report.exists():
        assert "residual:" not in report.read_text().lower()


def test_ac53_detect_failure_report_has_no_residual(tmp_path, monkeypatch):
    out = tmp_path / "out"
    _patch_ingest(monkeypatch, out)
    monkeypatch.setattr(
        run_module, "solve_pointing",
        lambda image_path, scale_hint: SolveResult(
            wcs=_tan_wcs(305.5565, -14.964, 64, 64, 2 / 3600), solve_seconds=0.0
        ),
    )
    monkeypatch.setattr(
        run_module, "detect_streak", lambda image_path: DetectFailure(reason="no linear features")
    )
    rc = main(["--image", "x.fits", "--meta", str(_META), "--out", str(out)])
    assert rc == 3
    assert not (out / "residual.txt").exists()
    report = out / "report.md"
    if report.exists():
        assert "residual:" not in report.read_text().lower()


def test_ac53_wrong_field_lock_report_has_no_residual(tmp_path, monkeypatch):
    out = tmp_path / "out"
    _patch_ingest(monkeypatch, out, shape=(6220, 6144))
    monkeypatch.setattr(
        run_module, "solve_pointing",
        lambda image_path, scale_hint: SolveResult(
            wcs=_tan_wcs(290.0, 0.0, 6144, 6220, 2 / 3600), solve_seconds=0.0
        ),
    )
    monkeypatch.setattr(
        run_module, "detect_streak",
        lambda image_path: StreakDetection(
            endpoints=((100.0, 100.0), (200.0, 200.0)), midpoint=(150.0, 150.0),
            angle_deg=45.0, length_px=141.0,
        ),
    )
    rc = main(["--image", "x.fits", "--meta", str(_META), "--out", str(out)])
    assert rc == 4
    assert not (out / "residual.txt").exists()
    report = out / "report.md"
    if report.exists():
        assert "residual:" not in report.read_text().lower()
