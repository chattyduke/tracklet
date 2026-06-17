#!/usr/bin/env python
"""fetch_fixtures — one-shot: freeze the TLE + Gaia cone snapshots (S1).

ONLINE; run once, then the pipeline runs fully offline against the committed fixtures.

What it does (in order):
  1. Fetch the real ISS TLE from CelesTrak (CATNR 25544).
  2. RESOLVE THE POINTING: propagate that TLE to the config's observation UTC with skyfield and
     take the ICRS RA/Dec the satellite is at as seen from the observer. That RA/Dec is the
     camera/scene CENTER (a PUBLIC scene parameter — where the camera points — NOT sealed truth;
     the sealed sat position `score` compares against is written ONLY by `render` in S2). Write the
     resolved center back into config/default_scene.toml so build_scene + offline downstream runs
     are self-consistent and the S2 streak lands in-frame.
  3. Fetch the Gaia DR3 cone at that resolved center (ROW_LIMIT=-1 -> no silent truncation).

Every fixture is provenance-stamped (source URL + exact query + UTC fetch time) and VALIDATED
before being written: a bad/HTML/short/bad-checksum TLE or an empty/truncated/mis-columned Gaia
CSV raises a hard error and writes NO snapshot. Idempotent: re-running overwrites cleanly.

scene.py stays PURE — no propagation lives there. Choosing the pointing here with skyfield does
NOT leak or pre-empt truth.json.

Run:  .venv/bin/python scripts/fetch_fixtures.py
"""
from __future__ import annotations

import datetime as _dt
import io
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

# python.org macOS builds ship a stdlib `ssl` with no CA bundle until "Install Certificates.command"
# is run, so live Gaia / CelesTrak queries fail cert verification. Point at certifi's (real, public)
# CA bundle so this works portably without disabling verification. (Mirrors scripts/_smoke_solve.py.)
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from tracklet import scene as _scene  # noqa: E402

CONFIG_PATH = _REPO / "config" / "default_scene.toml"
TLE_DIR = _REPO / "data" / "tle"
CAT_DIR = _REPO / "data" / "catalogue"

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR={catnr}&FORMAT=tle"
# Cone radius: half the field diagonal (~2.0 deg for the 2.844 deg field) plus margin.
CONE_RADIUS_DEG = 1.6
# Plausible-field floor: a 2.8 deg cone at mag<14 has thousands of Gaia sources; demand > a few hundred.
MIN_PLAUSIBLE_STARS = 300


# ---------------------------------------------------------------------------
# Validators (pure; fed text; raise ValueError on garbage). Reused by the write helpers.
# ---------------------------------------------------------------------------

def validate_tle_text(text: str) -> "_scene.TLE":
    """Validate TLE text (length + checksum + HTML-error-page reject). Raises ValueError on bad."""
    return _scene.parse_tle_text(text)


def validate_gaia_csv_text(text: str):
    """Validate Gaia CSV text -> astropy Table. Raises ValueError on empty / truncated / mis-columned.

    Rejects: missing required columns, zero rows, or an implausibly small star count (a truncated
    or failed pull). Provenance '#' header lines are treated as comments.
    """
    from astropy.io import ascii as ascii_io

    try:
        tbl = ascii_io.read(text.splitlines(), format="csv", comment=r"\s*#")
    except Exception as exc:  # noqa: BLE001 — any parse failure is a hard reject
        raise ValueError(f"Gaia CSV did not parse: {exc}") from exc
    required = {"ra", "dec", "phot_g_mean_mag"}
    if not required <= set(tbl.colnames):
        raise ValueError(
            f"Gaia CSV missing required columns {required - set(tbl.colnames)}; "
            f"got {tbl.colnames}"
        )
    if len(tbl) == 0:
        raise ValueError("Gaia CSV is empty (zero rows) — refusing to write a truncated star field")
    if len(tbl) < MIN_PLAUSIBLE_STARS:
        raise ValueError(
            f"Gaia CSV has only {len(tbl)} stars (< {MIN_PLAUSIBLE_STARS} plausible floor) — "
            "looks truncated; refusing to write"
        )
    return tbl


# ---------------------------------------------------------------------------
# Atomic, validate-then-write snapshot helpers (write NOTHING if validation fails).
# ---------------------------------------------------------------------------

def write_tle_snapshot(text: str, dest: str, provenance: str) -> "_scene.TLE":
    """Validate the TLE text, then atomically write `dest` with a provenance header. No write on fail."""
    tle = validate_tle_text(text)  # raises before any write
    body = f"# {provenance}\n{tle.name}\n{tle.line1}\n{tle.line2}\n" if tle.name else (
        f"# {provenance}\n{tle.line1}\n{tle.line2}\n"
    )
    _atomic_write(dest, body)
    return tle


def write_gaia_snapshot(text: str, dest: str, provenance: str):
    """Validate the Gaia CSV text, then atomically write `dest` with a provenance header. No write on fail."""
    tbl = validate_gaia_csv_text(text)  # raises before any write
    # Re-emit the validated table as canonical CSV with a leading provenance comment block.
    buf = io.StringIO()
    from astropy.io import ascii as ascii_io

    ascii_io.write(tbl, buf, format="csv")
    body = f"# {provenance}\n" + buf.getvalue()
    _atomic_write(dest, body)
    return tbl


def _atomic_write(dest: str, body: str) -> None:
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(body)
    os.replace(tmp, p)


# ---------------------------------------------------------------------------
# Online fetchers + pointing resolution.
# ---------------------------------------------------------------------------

def _http_get(url: str, attempts: int = 3) -> str:
    """GET with retry+backoff (CelesTrak/Gaia are flaky on this build). Returns decoded text."""
    last = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 — transient network errors are varied
            last = exc
            print(f"  GET attempt {attempt}/{attempts} failed ({type(exc).__name__}); retrying...")
            time.sleep(5 * attempt)
    raise RuntimeError(f"GET {url} failed after {attempts} attempts: {last}")


def fetch_tle(catnr: int) -> tuple[str, str]:
    """Return (tle_text, source_url)."""
    url = CELESTRAK_URL.format(catnr=catnr)
    return _http_get(url), url


def resolve_pointing(tle: "_scene.TLE", cfg: "_scene.SceneConfig") -> tuple[float, float]:
    """Propagate the TLE to cfg.utc as seen from the observer -> ICRS (RA, Dec) in degrees.

    Uses skyfield's topocentric (sat - observer).at(t).radec() with no epoch arg -> ICRS astrometric
    RA/Dec, the SAME frame the solver's WCS recovers (no truth/measured frame mismatch downstream).
    """
    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    t = _parse_utc(cfg.utc, ts)
    sat = EarthSatellite(tle.line1, tle.line2, tle.name or "sat", ts)
    observer = wgs84.latlon(cfg.observer_lat_deg, cfg.observer_lon_deg, cfg.observer_elev_m)
    ra, dec, _ = (sat - observer).at(t).radec()  # ICRS astrometric
    return float(ra._degrees), float(dec.degrees)


def _parse_utc(utc: str, ts):
    """Parse an ISO-8601 'Z' UTC string into a skyfield Time."""
    s = utc.replace("Z", "+00:00")
    dt = _dt.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return ts.from_datetime(dt)


def write_center_into_config(ra_deg: float, dec_deg: float) -> None:
    """Replace the center_ra_deg / center_dec_deg lines in default_scene.toml in place.

    A surgical line replacement (not a TOML re-serialize) keeps the human comments intact.
    """
    text = CONFIG_PATH.read_text()
    text = re.sub(
        r"(?m)^center_ra_deg\s*=.*$",
        f"center_ra_deg = {ra_deg:.6f}         # resolved by fetch_fixtures from the ISS TLE geometry",
        text,
    )
    text = re.sub(
        r"(?m)^center_dec_deg\s*=.*$",
        f"center_dec_deg = {dec_deg:.6f}",
        text,
    )
    CONFIG_PATH.write_text(text)


def fetch_gaia_cone(ra0: float, dec0: float, mag_limit: float) -> tuple[str, str]:
    """Fetch the Gaia DR3 cone CSV at the resolved center. Returns (csv_text, adql_query)."""
    from astroquery.gaia import Gaia

    Gaia.ROW_LIMIT = -1  # NO silent truncation — the default cap would chop the star field
    adql = (
        "SELECT ra, dec, phot_g_mean_mag FROM gaiadr3.gaia_source "
        f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra0},{dec0},{CONE_RADIUS_DEG})) "
        f"AND phot_g_mean_mag < {mag_limit}"
    )
    last = None
    for attempt in range(1, 4):
        try:
            tbl = Gaia.launch_job_async(adql).get_results()
            buf = io.StringIO()
            from astropy.io import ascii as ascii_io

            ascii_io.write(tbl["ra", "dec", "phot_g_mean_mag"], buf, format="csv")
            return buf.getvalue(), adql
        except Exception as exc:  # noqa: BLE001 — the Gaia archive is documented-unstable
            last = exc
            print(f"  Gaia query attempt {attempt}/3 failed ({type(exc).__name__}); retrying...")
            time.sleep(5 * attempt)
    raise RuntimeError(f"Gaia query failed after 3 attempts: {last}")


# ---------------------------------------------------------------------------
# Orchestrator.
# ---------------------------------------------------------------------------

def main() -> int:
    cfg = _scene.build_scene(str(CONFIG_PATH))
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()

    print(f"[1/3] fetching ISS TLE (CATNR {cfg.catnr}) from CelesTrak ...")
    tle_text, tle_url = fetch_tle(cfg.catnr)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d")
    tle_dest = TLE_DIR / f"iss_{stamp}.txt"
    tle = write_tle_snapshot(
        tle_text, str(tle_dest),
        provenance=f"source={tle_url} fetched_utc={now}",
    )
    print(f"      wrote {tle_dest.relative_to(_REPO)}")

    print("[2/3] resolving camera pointing from the TLE geometry (skyfield) ...")
    ra0, dec0 = resolve_pointing(tle, cfg)
    write_center_into_config(ra0, dec0)
    print(f"      center RA={ra0:.6f} deg  Dec={dec0:.6f} deg (written into config)")

    print(f"[3/3] fetching Gaia DR3 cone (r={CONE_RADIUS_DEG} deg, mag<{cfg.gaia_mag_limit}) ...")
    csv_text, adql = fetch_gaia_cone(ra0, dec0, cfg.gaia_mag_limit)
    safe_center = f"ra{ra0:.3f}_dec{dec0:.3f}".replace("-", "m")
    cat_dest = CAT_DIR / f"gaia_{safe_center}.csv"
    tbl = write_gaia_snapshot(
        csv_text, str(cat_dest),
        provenance=(
            f"source=gaiadr3.gaia_source via astroquery.Gaia(ROW_LIMIT=-1) "
            f"query=\"{adql}\" fetched_utc={now}"
        ),
    )
    print(f"      wrote {cat_dest.relative_to(_REPO)} ({len(tbl)} stars)")

    print("DONE — fixtures frozen + config pointing resolved; downstream runs fully offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
