"""M1 Sprint-3 real-truth tests — ACs 3.1, 3.2, 3.3, 3.5 (all NON-solver, offline).

These pin the real-frame satellite-truth assembly that the M0 `score` consumes UNCHANGED:
  * AC 3.1 — exposure MIDPOINT = DATE-OBS(start, UTC) + EXPTIME/2, robust ISO parse, fail-loud on
    ambiguity (a 1 s LEO timing error ~= arcminutes of along-track motion).
  * AC 3.2 — satellite RA/Dec via the SAME `render.propagate_satellite_radec` (topocentric site).
  * AC 3.3 — `truth.json` round-trips through `score._load_truth` with NO change to `score`.
  * AC 3.5 — the header WCS + midpoint are returned IN-MEMORY (never written into a solver image).

No network: the committed BW3 TLE + meta fixture drive everything; output goes to a pytest tmp_path.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_FIXTURES = _REPO / "tests" / "fixtures" / "real"


# ---------------------------------------------------------------------------
# AC 3.1 — exposure-midpoint timing semantics (DATE-OBS = start, UTC).
# ---------------------------------------------------------------------------


def test_exposure_midpoint_is_start_plus_half_exptime():
    from tracklet.realtruth import exposure_midpoint_utc

    mid = exposure_midpoint_utc("2022-11-18T02:47:16.782", 10.0)
    assert mid == dt.datetime(2022, 11, 18, 2, 47, 21, 782000, tzinfo=dt.timezone.utc)


def test_exposure_midpoint_parses_space_separated_and_no_fractional():
    from tracklet.realtruth import exposure_midpoint_utc

    # ISO with a space instead of 'T', no fractional seconds — still the UTC start.
    mid = exposure_midpoint_utc("2022-11-18 02:47:16", 10.0)
    assert mid == dt.datetime(2022, 11, 18, 2, 47, 21, tzinfo=dt.timezone.utc)


def test_exposure_midpoint_treats_naive_date_obs_as_utc():
    from tracklet.realtruth import exposure_midpoint_utc

    # DDOTI DATE-OBS carries no tz suffix; the convention is UTC — the result must be tz-aware UTC.
    mid = exposure_midpoint_utc("2022-11-18T02:47:16.782", 10.0)
    assert mid.tzinfo == dt.timezone.utc


def test_exposure_midpoint_fails_loud_on_unparseable_date_obs():
    from tracklet.realtruth import exposure_midpoint_utc

    with pytest.raises(ValueError):
        exposure_midpoint_utc("not-a-date", 10.0)


def test_exposure_midpoint_fails_loud_on_nonpositive_exptime():
    from tracklet.realtruth import exposure_midpoint_utc

    with pytest.raises(ValueError):
        exposure_midpoint_utc("2022-11-18T02:47:16.782", 0.0)
    with pytest.raises(ValueError):
        exposure_midpoint_utc("2022-11-18T02:47:16.782", -5.0)


# ---------------------------------------------------------------------------
# Fixtures for the full real-truth assembly (committed BW3 TLE + meta).
# ---------------------------------------------------------------------------


@pytest.fixture
def bw3_tle():
    from tracklet.scene import load_tle

    return load_tle(str(_FIXTURES / "bluewalker3_53807.tle"))


@pytest.fixture
def bw3_meta():
    import tomllib

    return tomllib.loads((_FIXTURES / "meta.toml").read_text())


# ---------------------------------------------------------------------------
# AC 3.2 — satellite RA/Dec via the SAME render.propagate_satellite_radec (topocentric).
# ---------------------------------------------------------------------------


def test_real_truth_uses_render_shared_propagation(bw3_tle, bw3_meta, tmp_path):
    from tracklet.realtruth import assemble_real_truth, exposure_midpoint_utc
    from tracklet.render import propagate_satellite_radec

    result = assemble_real_truth(bw3_tle, bw3_meta, tmp_path)

    obs = bw3_meta["observatory"]
    timing = bw3_meta["timing"]
    mid = exposure_midpoint_utc(timing["date_obs"], timing["exptime_s"])
    exp_ra, exp_dec = propagate_satellite_radec(
        bw3_tle, obs["lat_deg"], obs["lon_deg"], obs["elev_m"], mid
    )
    # The assembled scored truth IS the shared-helper propagation at the topocentric site/midpoint.
    assert result.scored_truth_ra_deg == pytest.approx(exp_ra, abs=1e-9)
    assert result.scored_truth_dec_deg == pytest.approx(exp_dec, abs=1e-9)


def test_real_truth_site_is_topocentric_not_geocentric(bw3_tle, bw3_meta, tmp_path):
    # Moving the observer materially (geocentre vs the real ~510 km LEO topocentric site) must
    # change the apparent RA/Dec — proving the propagation honors the site (LEO parallax).
    from tracklet.realtruth import assemble_real_truth, exposure_midpoint_utc
    from tracklet.render import propagate_satellite_radec

    result = assemble_real_truth(bw3_tle, bw3_meta, tmp_path)
    timing = bw3_meta["timing"]
    mid = exposure_midpoint_utc(timing["date_obs"], timing["exptime_s"])
    # A clearly different site (equator/prime-meridian/sea-level).
    geo_ra, geo_dec = propagate_satellite_radec(bw3_tle, 0.0, 0.0, 0.0, mid)
    import numpy as np

    sep_deg = np.hypot(result.scored_truth_ra_deg - geo_ra, result.scored_truth_dec_deg - geo_dec)
    assert sep_deg > 0.1  # parallax shift is large for a LEO object across two distant sites


# ---------------------------------------------------------------------------
# AC 3.3 — truth.json round-trips through score._load_truth with NO change to score.
# ---------------------------------------------------------------------------


def test_truth_json_consumed_by_score_load_truth_unchanged(bw3_tle, bw3_meta, tmp_path):
    from astropy.coordinates import SkyCoord

    from tracklet.realtruth import assemble_real_truth
    from tracklet.score import _load_truth

    result = assemble_real_truth(bw3_tle, bw3_meta, tmp_path)
    truth_path = tmp_path / "truth.json"
    assert truth_path.exists()

    coord = _load_truth(str(truth_path))
    assert isinstance(coord, SkyCoord)
    assert coord.ra.deg == pytest.approx(result.scored_truth_ra_deg, abs=1e-9)
    assert coord.dec.deg == pytest.approx(result.scored_truth_dec_deg, abs=1e-9)


def test_truth_json_scored_truth_schema_matches_render(bw3_tle, bw3_meta, tmp_path):
    # The on-disk schema key score reads is exactly render's: truth["scored_truth"]["ra_deg"/"dec_deg"].
    from tracklet.realtruth import assemble_real_truth

    assemble_real_truth(bw3_tle, bw3_meta, tmp_path)
    truth = json.loads((tmp_path / "truth.json").read_text())
    assert set(truth["scored_truth"]) == {"ra_deg", "dec_deg"}
    assert isinstance(truth["scored_truth"]["ra_deg"], float)
    assert isinstance(truth["scored_truth"]["dec_deg"], float)


# ---------------------------------------------------------------------------
# AC 3.5 — header WCS + midpoint returned IN-MEMORY (never written into a solver image).
# ---------------------------------------------------------------------------


def test_real_truth_returns_midpoint_in_memory(bw3_tle, bw3_meta, tmp_path):
    from tracklet.realtruth import assemble_real_truth, exposure_midpoint_utc

    result = assemble_real_truth(bw3_tle, bw3_meta, tmp_path)
    timing = bw3_meta["timing"]
    assert result.exposure_mid_utc == exposure_midpoint_utc(timing["date_obs"], timing["exptime_s"])


def test_real_truth_header_wcs_in_memory_absent_for_ddoti(bw3_tle, bw3_meta, tmp_path):
    # The DDOTI frame carries no header WCS (meta header_wcs_present=false) -> the in-memory
    # pointing_wcs is None. (When a frame DOES carry a header WCS, ingest passes it in-memory; the
    # assembler stores it on the result for the report diagnostic, never the solver.)
    from tracklet.realtruth import assemble_real_truth

    result = assemble_real_truth(bw3_tle, bw3_meta, tmp_path, pointing_wcs=None)
    assert result.pointing_wcs is None


def test_real_truth_writer_does_not_read_truth_token():
    # Seal: the realtruth source must not name the json-deserialize token (score is the sole reader).
    src = (_REPO / "src" / "tracklet" / "realtruth.py").read_text()
    assert "json.load" not in src
