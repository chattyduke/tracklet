"""M1 Sprint 1 — real-frame fixture integrity (non-solver, offline).

Sprint 1 adds NO product-module code: it acquires + smoke-verifies + locks the real frame and commits
the provenance fixtures (PROVENANCE.md, fetch.sh, the BW3 TLE, meta.toml). This test is the executable
Sprint-1 guard — it proves the committed fixtures are WELL-FORMED without needing the multi-MB frame
(which is gitignored and fetched on demand by fetch.sh). A fixture is the foundation of every downstream
M1 test; reject garbage before relying on it.

The live solve+detect smoke (AC 1.2 / AC 1.3) on the raw frame was run + recorded in PROVENANCE.md; the
end-to-end @solver proof on the *normalized* image is Sprint-2 AC 2.5 (binding) and Sprint-4 AC 4.1.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tracklet import scene

REPO = Path(__file__).resolve().parent.parent
REAL = REPO / "tests" / "fixtures" / "real"

DATE_OBS_START_UTC = "2022-11-18T02:47:16.782"  # DATE-OBS = exposure START; midpoint = start + EXPTIME/2 (pinned in Sprint 3)
MEMBER_SHA256 = "b6dcf797163fab78adca9316f0dcb18eb29e83c8c398ae325a292fad30519ca1"


# ---------------------------------------------------------------------------
# The committed BW3 TLE validates through the project's own checksum-gated parser (AC 1.4).
# ---------------------------------------------------------------------------

def test_committed_bw3_tle_loads_and_checksums():
    tle = scene.load_tle(str(REAL / "bluewalker3_53807.tle"))
    assert tle.name == "BLUEWALKER 3"
    assert tle.line1.startswith("1 53807U")
    assert tle.line2.startswith("2 53807")
    # parse_tle_text raised nothing → both lines are 69 chars and checksum-valid.


def test_committed_bw3_tle_epoch_is_near_the_exposure():
    """AC 1.4 — the TLE epoch is within a sane LEO range of DATE-OBS (not the far-epoch current TLE)."""
    from datetime import datetime, timedelta, timezone

    tle = scene.load_tle(str(REAL / "bluewalker3_53807.tle"))
    epoch_field = tle.line1[18:32]  # cols 19-32 (1-indexed): YYDDD.DDDDDDDD
    yy = int(epoch_field[:2])
    doy = float(epoch_field[2:])
    epoch = datetime(2000 + yy, 1, 1, tzinfo=timezone.utc) + timedelta(days=doy - 1)
    exposure = datetime.fromisoformat(DATE_OBS_START_UTC).replace(tzinfo=timezone.utc)
    days = abs((exposure - epoch).total_seconds()) / 86400.0
    assert days < 2.0, f"TLE epoch {days:.3f} d from the frame — too far for usable LEO SGP4"


# ---------------------------------------------------------------------------
# meta.toml is well-formed and matches the verified FITS header.
# ---------------------------------------------------------------------------

def test_meta_toml_parses_with_verified_header_values():
    meta = tomllib.loads((REAL / "meta.toml").read_text())
    assert meta["timing"]["date_obs"] == DATE_OBS_START_UTC
    assert meta["timing"]["exptime_s"] == 10.0
    assert meta["satellite"]["norad_id"] == 53807
    assert meta["satellite"]["name"] == "BLUEWALKER 3"
    assert meta["satellite"]["tle_file"] == "bluewalker3_53807.tle"
    assert meta["frame"]["member_sha256"] == MEMBER_SHA256
    # DDOTI carries no header WCS — the no-header-WCS pointing-truth adaptation is recorded.
    assert meta["pointing"]["header_wcs_present"] is False
    assert "commanded_ra_deg" in meta["pointing"]
    assert "commanded_dec_deg" in meta["pointing"]
    # The TLE file meta.toml names actually exists.
    assert (REAL / meta["satellite"]["tle_file"]).is_file()


def test_meta_observatory_site_confirmed_to_published_oan_spm():
    meta = tomllib.loads((REAL / "meta.toml").read_text())
    obs = meta["observatory"]
    assert -90 <= obs["lat_deg"] <= 90
    assert -180 <= obs["lon_deg"] <= 180
    assert obs["elev_m"] > 0
    # Sprint 3 (AC 3.2) CONFIRMED the site to the published OAN-SPM position (airmass.org /
    # OAN-UNAM); DDOTI sits on the OAN-SPM site. LEO parallax is material, so the value is pinned to
    # source — a future drift or un-confirmation must trip this guard.
    assert obs["site_confirmed"] is True
    assert obs["lat_deg"] == pytest.approx(31.044333, abs=1e-6)
    assert obs["lon_deg"] == pytest.approx(-115.46375, abs=1e-6)
    assert obs["elev_m"] == pytest.approx(2830.0, abs=1.0)


# ---------------------------------------------------------------------------
# fetch.sh pins the member SHA256 + two URLs (reproducibility survives URL rot).
# ---------------------------------------------------------------------------

def test_fetch_sh_pins_sha256_and_two_urls():
    body = (REAL / "fetch.sh").read_text()
    assert MEMBER_SHA256 in body, "fetch.sh must pin the member SHA256"
    assert body.count("zenodo.org") >= 2, "fetch.sh must carry two URLs (primary + mirror)"
    assert "8102655" in body, "fetch.sh must reference the Zenodo record"
    # Streams + extracts only the single member (never lands the 2.4 GB).
    assert "20221118T024706C1o.fits.fz" in body


# ---------------------------------------------------------------------------
# PROVENANCE.md records every AC-required field + the AC-1.5 sign-off.
# ---------------------------------------------------------------------------

def test_provenance_records_required_fields_and_signoff():
    prov = (REAL / "PROVENANCE.md").read_text()
    for needle in (
        "2022-11-18T02:47:16.782",   # DATE-OBS
        "10.0",                       # EXPTIME
        "53807",                      # NORAD id
        "22321.51776124",             # TLE epoch
        MEMBER_SHA256,                # member integrity
        "OAN-SPM",                    # observatory site
        "CC-BY-4.0",                  # licence
        "10.5281/zenodo.8102655",     # DOI
    ):
        assert needle in prov, f"PROVENANCE.md missing required field: {needle}"
    # AC 1.5 — human sign-off recorded.
    assert "AC-1.5 status: CLEARED" in prov
    # Header-WCS presence recorded (DDOTI has none → no-header-WCS adaptation).
    assert "Header WCS" in prov or "header WCS" in prov
