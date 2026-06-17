"""S1 AC 1.3 — fetch_fixtures' fetch-VALIDATION Poka-Yoke (offline; fed fakes only).

The fetch-time validators reject garbage BEFORE anything is written/committed:
- a malformed TLE (HTML error page / wrong-length lines / bad checksum) -> hard error;
- an empty / truncated Gaia CSV (missing columns / too few stars) -> hard error.

These tests feed in-memory fakes and NEVER hit the network. We also assert that on a validation
failure NO snapshot file is written (write happens only after validation passes).
"""
from __future__ import annotations

from pathlib import Path

import pytest

import scripts.fetch_fixtures as ff

# A real, valid ISS-style TLE pair (checksums correct) used as the "good" baseline.
_GOOD_TLE = (
    "ISS (ZARYA)\n"
    "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9009\n"
    "2 25544  51.6400 208.9163 0006703 130.5360 325.0288 15.49011323000008\n"
)


def test_validate_tle_accepts_good():
    tle = ff.validate_tle_text(_GOOD_TLE)
    assert tle.line1.startswith("1 25544")
    assert tle.line2.startswith("2 25544")


def test_validate_tle_rejects_html_error_page():
    with pytest.raises(ValueError):
        ff.validate_tle_text("<html><body>No GP data found</body></html>")


def test_validate_tle_rejects_wrong_length_line():
    short = _GOOD_TLE.replace(
        "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9009",
        "1 25544U 98067A   24001.5",
    )
    with pytest.raises(ValueError):
        ff.validate_tle_text(short)


def test_validate_tle_rejects_bad_checksum():
    # Flip the final checksum digit of line 2 (was 8) so the checksum no longer matches.
    bad = _GOOD_TLE.replace(
        "2 25544  51.6400 208.9163 0006703 130.5360 325.0288 15.49011323000008",
        "2 25544  51.6400 208.9163 0006703 130.5360 325.0288 15.49011323000005",
    )
    with pytest.raises(ValueError):
        ff.validate_tle_text(bad)


# ---- Gaia CSV validation ----

_GOOD_HEADER = "ra,dec,phot_g_mean_mag\n"


def _csv_with_n_rows(n: int) -> str:
    rows = "".join(f"{83.0 + i*1e-4},{-2.0 + i*1e-4},{10.0}\n" for i in range(n))
    return _GOOD_HEADER + rows


def test_validate_gaia_accepts_plausible_field():
    tbl = ff.validate_gaia_csv_text(_csv_with_n_rows(500))
    assert len(tbl) == 500


def test_validate_gaia_rejects_empty():
    with pytest.raises(ValueError):
        ff.validate_gaia_csv_text(_GOOD_HEADER)  # header only, zero rows


def test_validate_gaia_rejects_truncated_star_count():
    with pytest.raises(ValueError):
        ff.validate_gaia_csv_text(_csv_with_n_rows(5))  # implausibly few for the field


def test_validate_gaia_rejects_missing_columns():
    bad = "ra,dec\n" + "".join(f"{83.0+i*1e-4},{-2.0+i*1e-4}\n" for i in range(500))
    with pytest.raises(ValueError):
        ff.validate_gaia_csv_text(bad)


# ---- "no snapshot written on validation failure" ----

def test_write_tle_snapshot_writes_nothing_on_bad_tle(tmp_path):
    dest = tmp_path / "iss.txt"
    with pytest.raises(ValueError):
        ff.write_tle_snapshot("<html>nope</html>", str(dest), provenance="x")
    assert not dest.exists()


def test_write_gaia_snapshot_writes_nothing_on_bad_csv(tmp_path):
    dest = tmp_path / "gaia.csv"
    with pytest.raises(ValueError):
        ff.write_gaia_snapshot(_csv_with_n_rows(3), str(dest), provenance="x")
    assert not dest.exists()


def test_write_tle_snapshot_is_idempotent_on_good_tle(tmp_path):
    dest = tmp_path / "iss.txt"
    ff.write_tle_snapshot(_GOOD_TLE, str(dest), provenance="src=test query=test fetched=now")
    first = Path(dest).read_text()
    # Re-run overwrites cleanly with identical body (idempotent).
    ff.write_tle_snapshot(_GOOD_TLE, str(dest), provenance="src=test query=test fetched=now")
    assert Path(dest).read_text() == first
    # provenance is stamped into the file
    assert "src=test" in first
    # the validated element lines survive the write -> re-loadable by scene.load_tle
    from tracklet import scene
    tle = scene.load_tle(str(dest))
    assert tle.line1.startswith("1 25544")
