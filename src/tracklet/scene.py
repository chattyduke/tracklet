"""scene — single source of truth for scene parameters (S1).

`build_scene(config_path) -> SceneConfig` is PURE and reads NO truth: it loads the scene TOML,
validates it (fail-closed Poka-Yoke), and returns a frozen dataclass. The offline fixture loaders
(`load_tle` / `load_catalogue`) read the COMMITTED real-data snapshots under `data/` — they touch
no network and no `truth.json` (the sealed sat position is written only by `render` in S2).
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# SceneConfig — the frozen, single source of truth for scene parameters.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SceneConfig:
    """Immutable scene parameters loaded from config/default_scene.toml.

    `center_ra_deg`/`center_dec_deg` are the PUBLIC camera pointing (where the camera looks) —
    NOT sealed truth. fetch_fixtures resolves them from the TLE geometry and writes them back into
    the config so offline downstream runs are self-consistent.
    """

    # [satellite]
    satellite_name: str
    catnr: int
    # [observation]
    utc: str
    exposure_s: float
    # [observer]
    observer_lat_deg: float
    observer_lon_deg: float
    observer_elev_m: float
    # [camera]
    width_px: int
    height_px: int
    pixel_scale_arcsec: float
    center_ra_deg: float
    center_dec_deg: float
    fov_deg: float
    # [noise]
    psf_sigma_px: float
    read_noise_e: float
    gaia_mag_limit: float
    # [rng]
    seed: int


# Tolerance for the FOV / (W * pixel_scale) consistency check, in degrees.
# Generous enough to absorb rounding in the human-authored fov_deg, tight enough to catch a
# transposed or mistyped field (e.g. fov_deg=5 against a ~2.84 deg field).
_FOV_TOL_DEG = 1e-2
# A sane upper bound on a Gaia G magnitude limit for this proof (Gaia DR3 saturates ~3, the
# faint end is ~21; a limit above ~21 is meaningless here).
_MAX_MAG_LIMIT = 21.0


def _validate(cfg: SceneConfig) -> None:
    """Fail-closed Poka-Yoke. A bad / inconsistent config MUST raise (AC 1.1)."""
    if cfg.width_px <= 0 or cfg.height_px <= 0:
        raise ValueError(f"camera dims must be positive: {cfg.width_px}x{cfg.height_px}")
    if cfg.pixel_scale_arcsec <= 0:
        raise ValueError(f"pixel_scale_arcsec must be positive: {cfg.pixel_scale_arcsec}")
    if cfg.exposure_s <= 0:
        raise ValueError(f"exposure_s must be positive: {cfg.exposure_s}")
    if not (0.0 < cfg.gaia_mag_limit <= _MAX_MAG_LIMIT):
        raise ValueError(
            f"gaia_mag_limit must be in (0, {_MAX_MAG_LIMIT}]: {cfg.gaia_mag_limit}"
        )
    # Consistency: the declared field must match the geometry W * pixel_scale / 3600.
    derived_fov = cfg.width_px * cfg.pixel_scale_arcsec / 3600.0
    if abs(derived_fov - cfg.fov_deg) > _FOV_TOL_DEG:
        raise ValueError(
            f"fov_deg inconsistent with W*pixel_scale/3600: declared {cfg.fov_deg:.4f} deg, "
            f"derived {derived_fov:.4f} deg (tol {_FOV_TOL_DEG})"
        )


def build_scene(config_path: str) -> SceneConfig:
    """Load + validate the scene TOML into a frozen SceneConfig. Pure; reads no truth."""
    with open(config_path, "rb") as fh:
        raw = tomllib.load(fh)

    sat = raw["satellite"]
    obs = raw["observation"]
    site = raw["observer"]
    cam = raw["camera"]
    noise = raw["noise"]
    rng = raw["rng"]

    cfg = SceneConfig(
        satellite_name=str(sat["name"]),
        catnr=int(sat["catnr"]),
        utc=str(obs["utc"]),
        exposure_s=float(obs["exposure_s"]),
        observer_lat_deg=float(site["lat_deg"]),
        observer_lon_deg=float(site["lon_deg"]),
        observer_elev_m=float(site["elev_m"]),
        width_px=int(cam["width_px"]),
        height_px=int(cam["height_px"]),
        pixel_scale_arcsec=float(cam["pixel_scale_arcsec"]),
        center_ra_deg=float(cam["center_ra_deg"]),
        center_dec_deg=float(cam["center_dec_deg"]),
        fov_deg=float(cam["fov_deg"]),
        psf_sigma_px=float(noise["psf_sigma_px"]),
        read_noise_e=float(noise["read_noise_e"]),
        gaia_mag_limit=float(noise["gaia_mag_limit"]),
        seed=int(rng["seed"]),
    )
    _validate(cfg)
    return cfg


# ---------------------------------------------------------------------------
# Offline fixture loaders (read committed data/ snapshots — no network, no truth).
# ---------------------------------------------------------------------------

# The committed synthetic data fixtures (Gaia CSV + TLE) live at the repo-root `data/` in the dev
# tree, and a fresh CLONE has them by definition. A NON-editable wheel install lands in site-packages
# where the `__file__`-relative `_REPO/data` is absent, so an installed CLI resolves the fixtures via
# the TRACKLET_DATA env override — the documented clone→install→reproduce path (the S3 clean-room)
# sets it to the clone's `data/`. Default is the dev-tree `_REPO/data`, UNCHANGED for every existing
# dev / test / M0 / M1 path. This is fixture data, never `truth.json` — the seal is unaffected
# (scene reads no truth; only `score` deserializes the sealed truth).
_REPO = Path(__file__).resolve().parent.parent.parent
_DATA = Path(os.environ["TRACKLET_DATA"]) if os.environ.get("TRACKLET_DATA") else _REPO / "data"


@dataclass(frozen=True)
class TLE:
    """A parsed two-line element set (the two 69-char orbital element lines + optional name)."""

    name: str
    line1: str
    line2: str


def _tle_checksum_ok(line: str) -> bool:
    """TLE checksum: sum of digits (minus signs count as 1) mod 10 == last char (col 69)."""
    if len(line) != 69:
        return False
    total = 0
    for ch in line[:68]:
        if ch.isdigit():
            total += int(ch)
        elif ch == "-":
            total += 1
    return total % 10 == int(line[68])


def parse_tle_text(text: str) -> TLE:
    """Parse TLE text into a validated TLE. Raises ValueError on malformed / unchecksummed input.

    Accepts the CelesTrak 3-line form (name + line1 + line2) or a bare 2-line form. This is the
    shared validator used by both the offline loader and fetch_fixtures' fetch-time validation.
    """
    # Drop blank lines and provenance comment lines ('#') — the snapshot stamps a '# ...' header.
    lines = [
        ln.rstrip("\r\n")
        for ln in text.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    if not lines:
        raise ValueError("TLE is empty")
    # Reject the HTML error page CelesTrak returns on a bad CATNR / rate-limit.
    joined = text.lstrip().lower()
    if joined.startswith("<") or "<html" in joined or "no gp data" in joined:
        raise ValueError("TLE source returned an HTML/error page, not orbital elements")

    name = ""
    if not lines[0].startswith("1 "):
        # 3-line form: first line is the satellite name.
        name = lines[0].strip()
        elem = lines[1:]
    else:
        elem = lines
    if len(elem) < 2:
        raise ValueError(f"TLE must have two element lines; got {len(elem)}")
    line1, line2 = elem[0], elem[1]
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise ValueError("TLE element lines must start with '1 ' and '2 '")
    for ln in (line1, line2):
        if len(ln) != 69:
            raise ValueError(f"TLE element line must be 69 chars; got {len(ln)}: {ln!r}")
        if not _tle_checksum_ok(ln):
            raise ValueError(f"TLE checksum failed on line: {ln!r}")
    return TLE(name=name, line1=line1, line2=line2)


def load_tle(path: str) -> TLE:
    """Load + validate a committed TLE fixture from disk (offline). Raises on malformed input."""
    return parse_tle_text(Path(path).read_text())


def load_catalogue(path: str):
    """Load a committed Gaia CSV fixture (offline) -> astropy Table.

    Provenance header lines (prefixed '#') are comments and are skipped by the CSV reader.
    """
    from astropy.io import ascii as ascii_io  # local import: keep scene import light

    return ascii_io.read(Path(path).read_text().splitlines(), format="csv", comment=r"\s*#")


def default_tle_path(scene: SceneConfig) -> str:
    """Resolve the committed TLE fixture for this scene's satellite.

    fetch_fixtures keeps exactly ONE committed TLE (it replaces older snapshots on write), so there
    is normally a single candidate. If more than one is present (e.g. a stray file), prefer the
    newest by snapshot date so the resolution is deterministic.
    """
    cands = sorted((_DATA / "tle").glob("iss_*.txt")) if scene.catnr == 25544 else []
    if not cands:
        cands = sorted((_DATA / "tle").glob("*.txt"))
    if not cands:
        raise FileNotFoundError(f"no committed TLE fixture under {_DATA / 'tle'}")
    return str(cands[-1])


def _catalogue_center_from_name(path: Path) -> tuple[float, float] | None:
    """Parse the (ra, dec) center a `gaia_ra<RA>_dec<DEC>.csv` fixture name encodes ('m' = '-')."""
    import re

    m = re.match(r"gaia_ra([0-9.]+)_dec(m?[0-9.]+)\.csv$", path.name)
    if not m:
        return None
    ra = float(m.group(1))
    dec_tok = m.group(2)
    dec = -float(dec_tok[1:]) if dec_tok.startswith("m") else float(dec_tok)
    return ra, dec


def default_catalogue_path(scene: SceneConfig) -> str:
    """Resolve the committed Gaia CSV fixture whose center MATCHES the scene config.

    fetch_fixtures keeps exactly ONE committed catalogue (it replaces older snapshots on write).
    To be robust if more than one is present, pick the fixture whose name-encoded center is closest
    to the config center (deterministic) rather than a lexicographic `sorted()[-1]` (which could
    silently mismatch the pointing).
    """
    cands = sorted((_DATA / "catalogue").glob("gaia_*.csv"))
    if not cands:
        cands = sorted((_DATA / "catalogue").glob("*.csv"))
    if not cands:
        raise FileNotFoundError(f"no committed Gaia CSV fixture under {_DATA / 'catalogue'}")
    if len(cands) == 1:
        return str(cands[0])

    def _dist(p: Path) -> float:
        center = _catalogue_center_from_name(p)
        if center is None:
            return float("inf")
        ra, dec = center
        return (ra - scene.center_ra_deg) ** 2 + (dec - scene.center_dec_deg) ** 2

    return str(min(cands, key=_dist))
