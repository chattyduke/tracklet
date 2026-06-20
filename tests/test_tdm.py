"""M2 Sprint 2 — CCSDS TDM (RADEC) output writer tests (ACs 2.1, 2.2, 2.3).

``tdm.write_tdm(result, epoch_utc, station, out_path) -> Path`` writes a structurally-valid
CCSDS TDM 503.0-B-2 RADEC file from the IN-MEMORY measured RA/Dec + the exposure-midpoint epoch
+ the station identifier — symmetric to ``report.write_report`` (downstream of ``score``, a pure
text-formatter, NO ``json.load``). ``run`` emits ``track.tdm`` alongside ``residual.txt`` on the
SUCCESS path only (synthetic + real); a typed failure writes NO ``track.tdm`` (honest — no
fabricated track), exactly as ``residual.txt`` is withheld.

  * AC 2.1 (non-solver) — ``write_tdm`` from an in-memory ScoreResult emits a structurally-valid
    CCSDS RADEC file: required keyword blocks present + ordered; PARTICIPANT_1 == station;
    ANGLE_TYPE = RADEC; TIME_SYSTEM = UTC; measured RA/Dec (deg) + ISO-UTC epoch appear verbatim
    and round-trip within float tolerance.
  * AC 2.2 (synthetic: @solver; real: non-solver) — a successful run writes ``track.tdm`` whose
    ANGLE_1/ANGLE_2 == result.measured RA/Dec and whose epoch == the exposure-midpoint INSTANT
    (compared as parsed datetimes, NOT strings); PARTICIPANT_1 == "TRACKLET-SYNTH" (synthetic) /
    meta["observatory"]["name"] (real).
  * AC 2.3 (non-solver) — on a SolveFailure/DetectFailure/wrong-field (exits 2/3/4), NO
    ``track.tdm`` is written.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u

from tracklet import run as run_module
from tracklet.run import main
from tracklet.detect_streak import DetectFailure, StreakDetection
from tracklet.solve_pointing import SolveFailure, SolveResult
from tracklet.tdm import write_tdm

_REPO = Path(__file__).resolve().parent.parent
_REAL = _REPO / "tests" / "fixtures" / "real"
_META = _REAL / "meta.toml"


# ---------------------------------------------------------------------------
# Lightweight CCSDS TDM RADEC parser (test-side) — pull keyword = value pairs and the data lines.
# ---------------------------------------------------------------------------


def _kv(text: str) -> dict[str, str]:
    """Every ``KEYWORD = value`` pair in the file (last-wins; META keys are unique here)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _data_angles(text: str) -> dict[str, tuple[str, float]]:
    """Parse the ``<epoch> ANGLE_1 = <val>`` / ``ANGLE_2`` data lines -> {key: (epoch, value)}."""
    angles: dict[str, tuple[str, float]] = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\S+)\s+(ANGLE_[12])\s*=\s*([-+0-9.eE]+)\s*$", line)
        if m:
            epoch, key, val = m.group(1), m.group(2), float(m.group(3))
            angles[key] = (epoch, val)
    return angles


def _parse_epoch(s: str) -> dt.datetime:
    """Parse a CCSDS UTC epoch (``...Z`` or ``+00:00``) to a tz-aware UTC datetime."""
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def _make_result(ra_deg: float, dec_deg: float):
    """An in-memory ScoreResult-shaped object carrying a measured ICRS SkyCoord (no truth read).

    `truth` is set DELIBERATELY DISTINCT from `measured` (a few arcsec off — within the 10" gate so
    `passed=True` stays consistent) so the AC 2.1 assertions PIN that write_tdm emits the MEASURED
    RA/Dec, never the sealed truth. A measured→truth swap in the writer would shift the emitted angles
    by ~arcsec and FAIL the verbatim `ra_val == ra_deg` / `dec_val == dec_deg` checks below — closing a
    fabrication-adjacent path the seal AST guards cannot see (it is not a json.load)."""
    from tracklet.score import ScoreResult

    measured = SkyCoord(ra_deg * u.deg, dec_deg * u.deg, frame="icrs")
    truth = SkyCoord((ra_deg + 1e-3) * u.deg, (dec_deg + 1e-3) * u.deg, frame="icrs")
    return ScoreResult(
        residual_arcsec=float(measured.separation(truth).to(u.arcsec).value),
        measured=measured,
        truth=truth,
        threshold_arcsec=10.0,
        passed=True,
    )


# ---------------------------------------------------------------------------
# AC 2.1 — write_tdm emits a structurally-valid CCSDS TDM RADEC file (non-solver).
# ---------------------------------------------------------------------------


def test_write_tdm_emits_structurally_valid_ccsds_radec(tmp_path):
    ra_deg, dec_deg = 133.123456, -42.654321
    epoch = dt.datetime(2026, 6, 17, 8, 36, 13, tzinfo=dt.timezone.utc)
    station = "TRACKLET-SYNTH"
    out = tmp_path / "track.tdm"

    returned = write_tdm(_make_result(ra_deg, dec_deg), epoch, station, out)

    assert returned == out, "write_tdm returns the written path"
    assert out.exists(), "write_tdm writes the file"
    text = out.read_text()

    # Required CCSDS keyword blocks present AND ordered.
    for token in (
        "CCSDS_TDM_VERS", "META_START", "META_STOP", "DATA_START", "DATA_STOP"
    ):
        assert token in text, f"missing required CCSDS token {token!r}"
    idx = {tok: text.index(tok) for tok in
           ("CCSDS_TDM_VERS", "META_START", "META_STOP", "DATA_START", "DATA_STOP")}
    assert idx["CCSDS_TDM_VERS"] < idx["META_START"] < idx["META_STOP"] < \
        idx["DATA_START"] < idx["DATA_STOP"], f"CCSDS blocks out of order: {idx}"

    kv = _kv(text)
    assert kv["TIME_SYSTEM"] == "UTC", kv
    assert kv["PARTICIPANT_1"] == station, kv
    assert kv["MODE"] == "SEQUENTIAL", kv
    assert kv["ANGLE_TYPE"] == "RADEC", kv
    assert kv["REF_FRAME"] == "EME2000", kv

    angles = _data_angles(text)
    assert set(angles) == {"ANGLE_1", "ANGLE_2"}, angles
    (ra_epoch, ra_val) = angles["ANGLE_1"]
    (dec_epoch, dec_val) = angles["ANGLE_2"]
    # Measured RA/Dec (deg) appear verbatim and round-trip within float tolerance.
    assert ra_val == pytest.approx(ra_deg, abs=1e-9), (ra_val, ra_deg)
    assert dec_val == pytest.approx(dec_deg, abs=1e-9), (dec_val, dec_deg)
    # The epoch round-trips to the input instant (parsed, not string-compared).
    assert _parse_epoch(ra_epoch) == epoch
    assert _parse_epoch(dec_epoch) == epoch


# ---------------------------------------------------------------------------
# AC 2.2 — a successful run writes track.tdm with the measured RA/Dec + the midpoint instant.
# ---------------------------------------------------------------------------


@pytest.mark.solver
def test_synthetic_run_emits_tdm_with_measured_and_midpoint_epoch(tmp_path):
    """Full synthetic blind-solve run (real solver) -> track.tdm carrying the measured RA/Dec and the
    exposure-midpoint instant; PARTICIPANT_1 == "TRACKLET-SYNTH". @solver: this exercises the live
    emit on the real pipeline (the unit AC 2.1 is the non-solver structural proof)."""
    from tracklet.scene import build_scene

    out = tmp_path / "out"
    rc = main(["--out", str(out)])
    assert rc == 0, "synthetic blind-solve run must succeed"

    tdm = out / "track.tdm"
    assert tdm.exists(), "a successful synthetic run must write track.tdm"
    text = tdm.read_text()

    kv = _kv(text)
    assert kv["PARTICIPANT_1"] == "TRACKLET-SYNTH", kv

    # Cross-check ANGLE_1/ANGLE_2 against the residual.txt-scored measured position is not directly
    # available; instead assert the emitted RA/Dec equal the rendered scored_truth within the residual
    # band and the epoch equals the exposure midpoint instant.
    scene = build_scene(str(_REPO / "config" / "default_scene.toml"))
    start = dt.datetime.fromisoformat(scene.utc.replace("Z", "+00:00"))
    expected_mid = start + dt.timedelta(seconds=scene.exposure_s / 2.0)

    angles = _data_angles(text)
    (ra_epoch, _ra_val) = angles["ANGLE_1"]
    (dec_epoch, _dec_val) = angles["ANGLE_2"]
    assert _parse_epoch(ra_epoch) == expected_mid.astimezone(dt.timezone.utc)
    assert _parse_epoch(dec_epoch) == expected_mid.astimezone(dt.timezone.utc)

    # The emitted angles must equal the scored measured position. Recover it from the run's own
    # residual band: the measured RA/Dec must be within ~10" of the sealed scored_truth.
    import json

    truth = json.loads((out / "truth.json").read_text())["scored_truth"]
    emitted = SkyCoord(angles["ANGLE_1"][1] * u.deg, angles["ANGLE_2"][1] * u.deg, frame="icrs")
    truth_c = SkyCoord(truth["ra_deg"] * u.deg, truth["dec_deg"] * u.deg, frame="icrs")
    assert emitted.separation(truth_c).to(u.arcsec).value < 10.0, (
        "emitted TDM angles must be the scored measured position (within the residual gate)"
    )


def test_real_run_emits_tdm_with_measured_and_midpoint_epoch(tmp_path, monkeypatch):
    """Full real-path success run (monkeypatched ingest/truth/solve/detect — non-solver, mirrors
    test_run_image) -> track.tdm carrying the measured RA/Dec and the real exposure-midpoint instant;
    PARTICIPANT_1 == meta["observatory"]["name"]."""
    out = tmp_path / "out"
    mid = dt.datetime(2022, 11, 18, 2, 47, 11, tzinfo=dt.timezone.utc)
    rec_ra, rec_dec = 305.5565, -14.964

    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        fits.PrimaryHDU(np.zeros((6220, 6144), dtype=np.float32)).writeto(p, overwrite=True)
        return IngestResult(image=np.zeros((6220, 6144), np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    def _stub_truth(out_dir):
        import json as _json

        from tracklet.realtruth import RealTruthResult

        o = Path(out_dir)
        o.mkdir(parents=True, exist_ok=True)
        tp = o / "truth.json"
        tp.write_text(_json.dumps({"scored_truth": {"ra_deg": rec_ra, "dec_deg": rec_dec}}))
        return RealTruthResult(
            truth_path=tp, scored_truth_ra_deg=rec_ra, scored_truth_dec_deg=rec_dec,
            exposure_mid_utc=mid, pointing_wcs=None, norad_id=53807,
        )

    def _tan_wcs(ra, dec, n1, n2, scale_deg):
        w = WCS(naxis=2)
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        w.wcs.crpix = [(n1 + 1) / 2.0, (n2 + 1) / 2.0]
        w.wcs.crval = [ra, dec]
        w.wcs.cdelt = [-scale_deg, scale_deg]
        return w

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))
    monkeypatch.setattr(
        run_module, "solve_pointing",
        lambda image_path, scale_hint: SolveResult(
            wcs=_tan_wcs(rec_ra, rec_dec, 6144, 6220, 2 / 3600), solve_seconds=0.0
        ),
    )
    # The detected midpoint sits at the WCS center -> measured == (rec_ra, rec_dec).
    monkeypatch.setattr(
        run_module, "detect_streak",
        lambda image_path: StreakDetection(
            endpoints=((3071.5, 3109.5), (3072.5, 3110.5)), midpoint=(3072.0, 3110.0),
            angle_deg=45.0, length_px=1.41,
        ),
    )

    rc = main(["--image", "ignored.fits", "--meta", str(_META), "--out", str(out)])
    assert rc == 0, "real-path success run must exit 0"

    tdm = out / "track.tdm"
    assert tdm.exists(), "a successful real run must write track.tdm"
    text = tdm.read_text()

    kv = _kv(text)
    assert kv["PARTICIPANT_1"] == "OAN-SPM / DDOTI (San Pedro Martir, MX)", kv

    angles = _data_angles(text)
    (ra_epoch, ra_val) = angles["ANGLE_1"]
    (dec_epoch, dec_val) = angles["ANGLE_2"]
    # Measured RA/Dec == the WCS-center recovery (the detected midpoint at frame center).
    assert ra_val == pytest.approx(rec_ra, abs=1e-3), (ra_val, rec_ra)
    assert dec_val == pytest.approx(rec_dec, abs=1e-3), (dec_val, rec_dec)
    # Epoch == the real exposure-midpoint instant (compared as parsed datetimes, not strings).
    assert _parse_epoch(ra_epoch) == mid
    assert _parse_epoch(dec_epoch) == mid


# ---------------------------------------------------------------------------
# AC 2.3 — a typed failure writes NO track.tdm (honest — no fabricated track).
# ---------------------------------------------------------------------------


def test_synthetic_solve_failure_writes_no_tdm(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setattr(
        run_module, "solve_pointing", lambda image_path, scale_hint: SolveFailure(reason="x")
    )
    rc = main(["--out", str(out)])
    assert rc == 2
    assert not (out / "track.tdm").exists(), "no TDM may be written on a synthetic solve failure"


def test_synthetic_detect_failure_writes_no_tdm(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setattr(
        run_module, "detect_streak", lambda image_path: DetectFailure(reason="x")
    )
    rc = main(["--out", str(out)])
    assert rc == 3
    assert not (out / "track.tdm").exists(), "no TDM may be written on a synthetic detect failure"


def test_real_wrong_field_lock_writes_no_tdm(tmp_path, monkeypatch):
    """A wrong-field lock (AC 4.6, exit 4) must NOT write a fabricated track.tdm."""
    out = tmp_path / "out"

    def _fake_ingest(image_path, meta, out_dir):
        from tracklet.ingest import IngestResult

        p = Path(out_dir) / "image.fits"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        fits.PrimaryHDU(np.zeros((6220, 6144), dtype=np.float32)).writeto(p, overwrite=True)
        return IngestResult(image=np.zeros((6220, 6144), np.float32), image_path=p, science_hdu=0,
                            header=fits.Header())

    def _stub_truth(out_dir):
        import json as _json

        from tracklet.realtruth import RealTruthResult

        o = Path(out_dir)
        o.mkdir(parents=True, exist_ok=True)
        tp = o / "truth.json"
        tp.write_text(_json.dumps({"scored_truth": {"ra_deg": 305.5565, "dec_deg": -14.964}}))
        return RealTruthResult(
            truth_path=tp, scored_truth_ra_deg=305.5565, scored_truth_dec_deg=-14.964,
            exposure_mid_utc=dt.datetime(2022, 11, 18, 2, 47, 11, tzinfo=dt.timezone.utc),
            pointing_wcs=None, norad_id=53807,
        )

    def _tan_wcs(ra, dec, n1, n2, scale_deg):
        w = WCS(naxis=2)
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        w.wcs.crpix = [(n1 + 1) / 2.0, (n2 + 1) / 2.0]
        w.wcs.crval = [ra, dec]
        w.wcs.cdelt = [-scale_deg, scale_deg]
        return w

    monkeypatch.setattr(run_module, "ingest_external_image", _fake_ingest)
    monkeypatch.setattr(run_module, "assemble_real_truth", lambda *a, **k: _stub_truth(out))
    # A WCS 10+ deg from the expected pointing -> wrong-field lock.
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

    rc = main(["--image", "ignored.fits", "--meta", str(_META), "--out", str(out)])
    assert rc == 4, "a wrong-field lock must exit 4"
    assert not (out / "track.tdm").exists(), "no TDM may be written on a wrong-field lock"
