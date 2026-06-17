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


# ---------------------------------------------------------------------------
# F1 + F2 — visible-pass resolution + fail-closed below-horizon Poka-Yoke.
#
# The committed ISS TLE (epoch ~2026-06-16T20:48Z) is propagated only to obs times
# WITHIN ~1 day of its epoch, and ONLY to times where the ISS is genuinely above the
# horizon (alt > 20 deg) over the Perth observer. A below-horizon or far-from-epoch
# time must HARD-FAIL — a starless / fictional-SGP4 scene must never be frozen.
# ---------------------------------------------------------------------------

import dataclasses  # noqa: E402

from tracklet import scene as _sc  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO / "config" / "default_scene.toml"

# The committed real ISS TLE fixture (epoch ~2026-06-16T20:48Z).
_REAL_TLE = _sc.load_tle(str(REPO / "data" / "tle" / "iss_20260617.txt"))


def _cfg_with_utc(utc: str) -> "_sc.SceneConfig":
    base = _sc.build_scene(str(DEFAULT_CONFIG))
    return dataclasses.replace(base, utc=utc)


def test_iss_altitude_at_midpoint_helper_matches_skyfield():
    # The committed config's obs time must put the ISS genuinely above the horizon.
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    alt = ff.iss_altitude_deg(_REAL_TLE, cfg)
    assert alt > 20.0


def test_assert_above_horizon_rejects_old_far_side_time():
    # The OLD committed obs time (2026-06-01T14:00Z) is ~15 days before epoch and puts
    # the ISS at altitude ~-85 deg (far side of Earth). It MUST hard-fail, no snapshot.
    cfg = _cfg_with_utc("2026-06-01T14:00:00Z")
    with pytest.raises(ValueError):
        ff.assert_pass_is_visible(_REAL_TLE, cfg)


def test_assert_above_horizon_accepts_committed_visible_pass():
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    # Does not raise; returns the (positive) altitude it asserted on.
    alt = ff.assert_pass_is_visible(_REAL_TLE, cfg)
    assert alt > 20.0


def test_obs_time_is_within_a_day_of_tle_epoch():
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    # Folds in F2: SGP4 is fiction far from epoch — keep the scene obs time within ~1 day.
    assert ff.abs_days_from_epoch(_REAL_TLE, cfg.utc) < 1.0


def test_resolve_pointing_centers_on_exposure_midpoint():
    # Per the plan's truth-at-midpoint convention: config `utc` is the exposure START,
    # the pointing centers on the ISS position at the exposure MIDPOINT (start + exp/2).
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    ra_mid, dec_mid = ff.resolve_pointing(_REAL_TLE, cfg)
    # The committed center must equal the midpoint pointing (config is self-consistent).
    assert cfg.center_ra_deg == pytest.approx(ra_mid, abs=1e-3)
    assert cfg.center_dec_deg == pytest.approx(dec_mid, abs=1e-3)
    # And the midpoint != the start position (exposure window actually straddles).
    ra_start, dec_start = ff.resolve_pointing_at(_REAL_TLE, cfg, cfg.utc)
    assert (ra_mid, dec_mid) != (ra_start, dec_start)


# ---------------------------------------------------------------------------
# F3 — Gaia cone radius must cover the field half-diagonal (corner stars).
# ---------------------------------------------------------------------------

def test_cone_radius_covers_field_half_diagonal():
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    import math
    half_diag = math.sqrt(2.0) * cfg.fov_deg / 2.0  # ~2.011 deg for the 2.844 deg field
    assert ff.CONE_RADIUS_DEG >= half_diag


def test_committed_catalogue_has_stars_in_all_four_frame_corners():
    # The cone must be wide enough that every projected frame corner has nearby Gaia stars
    # (no starless corners). Check angular separation, not just the cone radius constant.
    import math
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    cat = _sc.load_catalogue(_sc.default_catalogue_path(cfg))
    ra0 = math.radians(cfg.center_ra_deg)
    dec0 = math.radians(cfg.center_dec_deg)
    half = cfg.fov_deg / 2.0
    ras = [math.radians(float(r)) for r in cat["ra"]]
    decs = [math.radians(float(d)) for d in cat["dec"]]

    def sep_deg(r1, d1, r2, d2):
        # great-circle separation in degrees
        v = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
        return math.degrees(math.acos(max(-1.0, min(1.0, v))))

    # four corners offset by +-half in a local tangent frame
    for dra, ddec in ((-half, -half), (half, -half), (-half, half), (half, half)):
        cdec = math.radians(cfg.center_dec_deg + ddec)
        cra = math.radians(cfg.center_ra_deg + dra / max(math.cos(dec0), 1e-6))
        nearest = min(sep_deg(cra, cdec, r, d) for r, d in zip(ras, decs))
        assert nearest < 0.5, f"corner ({dra},{ddec}) has nearest star {nearest:.2f} deg away"


# ---------------------------------------------------------------------------
# F4 — single committed fixture set + deterministic config-matching resolution.
# ---------------------------------------------------------------------------

def test_exactly_one_committed_tle_and_one_catalogue():
    tles = sorted((REPO / "data" / "tle").glob("*.txt"))
    cats = sorted((REPO / "data" / "catalogue").glob("*.csv"))
    assert len(tles) == 1, f"expected exactly one committed TLE, got {tles}"
    assert len(cats) == 1, f"expected exactly one committed catalogue, got {cats}"


def test_default_catalogue_path_matches_config_center():
    # default_catalogue_path must resolve to the fixture whose center matches the config,
    # not lexicographic sorted()[-1] (which can mismatch).
    cfg = _sc.build_scene(str(DEFAULT_CONFIG))
    path = Path(_sc.default_catalogue_path(cfg))
    # the resolved catalogue's stars must surround the config center (mean within ~1 deg)
    import math
    cat = _sc.load_catalogue(str(path))
    mean_ra = sum(float(r) for r in cat["ra"]) / len(cat)
    mean_dec = sum(float(d) for d in cat["dec"]) / len(cat)
    assert abs(mean_ra - cfg.center_ra_deg) < 1.0
    assert abs(mean_dec - cfg.center_dec_deg) < 1.0


def test_clean_fixture_dir_removes_orphans(tmp_path):
    # _replace_only writes the new file AND removes stale siblings matching the glob.
    d = tmp_path / "catalogue"
    d.mkdir()
    (d / "gaia_old1.csv").write_text("# stale\nra,dec,phot_g_mean_mag\n")
    (d / "gaia_old2.csv").write_text("# stale\nra,dec,phot_g_mean_mag\n")
    new = d / "gaia_new.csv"
    ff._replace_only(str(new), "# fresh\nra,dec,phot_g_mean_mag\n", glob="gaia_*.csv")
    remaining = sorted(p.name for p in d.glob("gaia_*.csv"))
    assert remaining == ["gaia_new.csv"]


# ---------------------------------------------------------------------------
# F5 — negative-coordinate filename mangle only touches the dec component.
# ---------------------------------------------------------------------------

def test_catalogue_filename_mangles_only_dec_sign():
    # A negative Dec must mangle to 'm' WITHOUT touching anything else in the name.
    name = ff.catalogue_filename(133.86, -42.59)
    assert name == "gaia_ra133.860_decm42.590.csv"
    # A positive Dec leaves no 'm'.
    name_pos = ff.catalogue_filename(35.528, 26.548)
    assert name_pos == "gaia_ra35.528_dec26.548.csv"
