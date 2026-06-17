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
# Cone radius MUST cover the field half-diagonal so no frame CORNER is starless. The field is
# square (W*pixel_scale/3600 ~= 2.844 deg per side), so the half-diagonal is sqrt(2)*fov/2 ~=
# 2.011 deg. 2.1 deg adds a small margin (projection/edge slop) on top of that. A radius < the
# half-diagonal would leave the four corners outside the cone -> starless corners (review F3).
CONE_RADIUS_DEG = 2.1
# Plausible-field floor: a 2.8 deg cone at mag<14 has thousands of Gaia sources; demand > a few hundred.
MIN_PLAUSIBLE_STARS = 300
# Minimum ISS altitude (deg) over the observer for a scene to be considered a real visible pass.
# Below this the satellite is too low / below the horizon to image — freezing such a scene would
# bake a fictional below-horizon geometry into every downstream test (review F1).
MIN_PASS_ALT_DEG = 20.0
# SGP4 is only trustworthy near the TLE epoch; refuse obs times further than this from epoch (F2).
MAX_DAYS_FROM_EPOCH = 1.0


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
    # Keep exactly one committed TLE fixture (F4): replace any older iss_*.txt siblings.
    _replace_only(dest, body, glob="*.txt")
    return tle


def write_gaia_snapshot(text: str, dest: str, provenance: str):
    """Validate the Gaia CSV text, then atomically write `dest` with a provenance header. No write on fail."""
    tbl = validate_gaia_csv_text(text)  # raises before any write
    # Re-emit the validated table as canonical CSV with a leading provenance comment block.
    buf = io.StringIO()
    from astropy.io import ascii as ascii_io

    ascii_io.write(tbl, buf, format="csv")
    body = f"# {provenance}\n" + buf.getvalue()
    # Keep exactly one committed catalogue fixture (F4): replace any older gaia_*.csv siblings.
    _replace_only(dest, body, glob="*.csv")
    return tbl


def _atomic_write(dest: str, body: str) -> None:
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(body)
    os.replace(tmp, p)


def _replace_only(dest: str, body: str, glob: str) -> None:
    """Atomically write `dest`, then delete every OTHER file in its dir matching `glob`.

    Keeps exactly ONE committed fixture per kind (review F4): re-fetching at a new center/date
    no longer orphans the previous snapshot, so default_*_path can never resolve a stale file.
    """
    _atomic_write(dest, body)
    p = Path(dest)
    for sib in p.parent.glob(glob):
        if sib.resolve() != p.resolve():
            sib.unlink()


def catalogue_filename(ra_deg: float, dec_deg: float) -> str:
    """Deterministic Gaia fixture filename for a center, mangling ONLY the Dec sign (review F5).

    A negative Dec -> 'decm<abs>'; the leading-'-' is mangled on the Dec COMPONENT alone, never
    over the whole string (the old `.replace('-', 'm')` only worked because RA happened to be >= 0).
    """
    dec_tok = f"m{abs(dec_deg):.3f}" if dec_deg < 0 else f"{dec_deg:.3f}"
    return f"gaia_ra{ra_deg:.3f}_dec{dec_tok}.csv"


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


def _build_sat_observer(tle: "_scene.TLE", cfg: "_scene.SceneConfig"):
    """Construct (timescale, EarthSatellite, observer) once for the geometry helpers."""
    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    sat = EarthSatellite(tle.line1, tle.line2, tle.name or "sat", ts)
    observer = wgs84.latlon(cfg.observer_lat_deg, cfg.observer_lon_deg, cfg.observer_elev_m)
    return ts, sat, observer


def _exposure_midpoint_utc(cfg: "_scene.SceneConfig") -> str:
    """The exposure MIDPOINT UTC = config `utc` (exposure START) + exposure_s/2.

    Per the plan's truth-at-midpoint convention (Sprint 2): truth = sat RA/Dec at exposure
    midpoint, so the PUBLIC camera pointing also centers on the midpoint position.
    """
    start = _parse_dt(cfg.utc)
    mid = start + _dt.timedelta(seconds=cfg.exposure_s / 2.0)
    return mid.isoformat().replace("+00:00", "Z")


def resolve_pointing_at(
    tle: "_scene.TLE", cfg: "_scene.SceneConfig", utc: str
) -> tuple[float, float]:
    """Propagate the TLE to a SPECIFIC UTC -> ICRS (RA, Dec) in degrees, seen from the observer.

    Uses skyfield's topocentric (sat - observer).at(t).radec() with no epoch arg -> ICRS astrometric
    RA/Dec, the SAME frame the solver's WCS recovers (no truth/measured frame mismatch downstream).
    """
    ts, sat, observer = _build_sat_observer(tle, cfg)
    t = _to_time(utc, ts)
    ra, dec, _ = (sat - observer).at(t).radec()  # ICRS astrometric
    return float(ra._degrees), float(dec.degrees)


def resolve_pointing(tle: "_scene.TLE", cfg: "_scene.SceneConfig") -> tuple[float, float]:
    """Resolve the camera center = the ISS ICRS RA/Dec at the EXPOSURE MIDPOINT (truth convention)."""
    return resolve_pointing_at(tle, cfg, _exposure_midpoint_utc(cfg))


def iss_altitude_deg(tle: "_scene.TLE", cfg: "_scene.SceneConfig", utc: str | None = None) -> float:
    """ISS altitude (deg) over the observer at the given UTC (default: the exposure midpoint)."""
    ts, sat, observer = _build_sat_observer(tle, cfg)
    t = _to_time(utc or _exposure_midpoint_utc(cfg), ts)
    alt, _az, _d = (sat - observer).at(t).altaz()
    return float(alt.degrees)


def abs_days_from_epoch(tle: "_scene.TLE", utc: str) -> float:
    """|utc - TLE epoch| in days. SGP4 is fiction far from epoch -> the obs time must stay close."""
    from skyfield.api import EarthSatellite, load

    ts = load.timescale()
    sat = EarthSatellite(tle.line1, tle.line2, tle.name or "sat", ts)
    epoch = sat.epoch.utc_datetime()
    return abs((_parse_dt(utc) - epoch).total_seconds()) / 86400.0


def assert_pass_is_visible(tle: "_scene.TLE", cfg: "_scene.SceneConfig") -> float:
    """Fail-closed Poka-Yoke (review F1+F2): the obs time MUST be a REAL visible pass near epoch.

    Raises ValueError if the ISS is below MIN_PASS_ALT_DEG at the exposure midpoint, OR if the obs
    time is further than MAX_DAYS_FROM_EPOCH from the TLE epoch. A below-horizon or far-from-epoch
    scene must NEVER be frozen — it would bake fictional SGP4 geometry into every downstream test.
    Returns the asserted (positive) altitude on success.
    """
    days = abs_days_from_epoch(tle, cfg.utc)
    if days > MAX_DAYS_FROM_EPOCH:
        raise ValueError(
            f"obs time {cfg.utc} is {days:.2f} days from the TLE epoch "
            f"(> {MAX_DAYS_FROM_EPOCH} d) — SGP4 is unreliable that far out; refusing to freeze"
        )
    alt = iss_altitude_deg(tle, cfg)
    if alt <= MIN_PASS_ALT_DEG:
        raise ValueError(
            f"ISS altitude at the exposure midpoint is {alt:.2f} deg "
            f"(<= {MIN_PASS_ALT_DEG} deg horizon floor) — not a visible pass; refusing to freeze "
            "a below-horizon scene"
        )
    return alt


def _parse_dt(utc: str) -> _dt.datetime:
    """Parse an ISO-8601 'Z' UTC string into a timezone-aware datetime."""
    s = utc.replace("Z", "+00:00")
    d = _dt.datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return d


def _to_time(utc: str, ts):
    """Parse an ISO-8601 'Z' UTC string into a skyfield Time."""
    return ts.from_datetime(_parse_dt(utc))


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
    # Fail-closed BEFORE resolving/fetching: the config obs time MUST be a real visible pass near
    # epoch (review F1+F2). A below-horizon / far-from-epoch scene raises here and freezes nothing.
    alt = assert_pass_is_visible(tle, cfg)
    print(
        f"      visible-pass check OK: ISS alt={alt:.2f} deg at exposure midpoint "
        f"({_exposure_midpoint_utc(cfg)}), {abs_days_from_epoch(tle, cfg.utc):.2f} d from epoch"
    )
    ra0, dec0 = resolve_pointing(tle, cfg)  # center = ISS RA/Dec at the exposure MIDPOINT
    write_center_into_config(ra0, dec0)
    print(f"      center RA={ra0:.6f} deg  Dec={dec0:.6f} deg (written into config)")

    print(f"[3/3] fetching Gaia DR3 cone (r={CONE_RADIUS_DEG} deg, mag<{cfg.gaia_mag_limit}) ...")
    csv_text, adql = fetch_gaia_cone(ra0, dec0, cfg.gaia_mag_limit)
    cat_dest = CAT_DIR / catalogue_filename(ra0, dec0)
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
