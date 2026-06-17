"""S1 — scene.SceneConfig + build_scene + offline fixture loaders.

ACs:
- 1.1: SceneConfig deterministic; validation REJECTS an inconsistent FOV/pixel-scale/dims config;
  the FOV math (W * pixel_scale / 3600 ~= FOV) is checked.
- 1.2: the frozen TLE + Gaia CSV load OFFLINE (loaders read committed fixtures, no network).

All offline: against the committed config/fixtures or fed in-memory fakes. NO network in this path.
"""
from __future__ import annotations

import dataclasses
import textwrap
from pathlib import Path

import pytest

from tracklet import scene

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO / "config" / "default_scene.toml"


# ---------------------------------------------------------------------------
# AC 1.1 — SceneConfig deterministic + validation Poka-Yoke + FOV math
# ---------------------------------------------------------------------------

def test_build_scene_loads_default_config_deterministically():
    a = scene.build_scene(str(DEFAULT_CONFIG))
    b = scene.build_scene(str(DEFAULT_CONFIG))
    assert a == b  # frozen dataclass equality — deterministic, pure
    # spot-check the scene parameters round-tripped from the TOML
    assert a.catnr == 25544
    assert a.width_px == 2048
    assert a.height_px == 2048
    assert a.pixel_scale_arcsec == pytest.approx(5.0)
    assert a.exposure_s == pytest.approx(2.0)
    assert a.gaia_mag_limit == pytest.approx(14.0)
    assert a.seed == 20260601
    assert a.observer_lat_deg == pytest.approx(-31.95)
    assert a.observer_lon_deg == pytest.approx(115.86)


def test_sceneconfig_is_frozen():
    cfg = scene.build_scene(str(DEFAULT_CONFIG))
    assert dataclasses.is_dataclass(cfg)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.width_px = 1  # type: ignore[misc]


def test_fov_math_consistency_holds_for_default_config():
    cfg = scene.build_scene(str(DEFAULT_CONFIG))
    expected_fov = cfg.width_px * cfg.pixel_scale_arcsec / 3600.0
    assert cfg.fov_deg == pytest.approx(expected_fov, abs=1e-2)


def _write_toml(tmp_path: Path, body: str) -> str:
    p = tmp_path / "scene.toml"
    p.write_text(textwrap.dedent(body))
    return str(p)


_GOOD_TOML = """\
[satellite]
name = "ISS (ZARYA)"
catnr = 25544
[observation]
utc = "2026-06-01T14:00:00Z"
exposure_s = 2.0
[observer]
lat_deg = -31.95
lon_deg = 115.86
elev_m = 10.0
[camera]
width_px = 2048
height_px = 2048
pixel_scale_arcsec = 5.0
center_ra_deg = 83.8
center_dec_deg = -2.0
fov_deg = 2.844
[noise]
psf_sigma_px = 1.5
read_noise_e = 5.0
gaia_mag_limit = 14.0
[rng]
seed = 20260601
"""


def test_good_config_round_trips(tmp_path):
    cfg = scene.build_scene(_write_toml(tmp_path, _GOOD_TOML))
    assert cfg.center_ra_deg == pytest.approx(83.8)
    assert cfg.center_dec_deg == pytest.approx(-2.0)


def test_validation_rejects_inconsistent_fov(tmp_path):
    # fov_deg deliberately wrong (claims 5 deg; W*scale/3600 ~= 2.84 deg) -> must raise.
    bad = _GOOD_TOML.replace("fov_deg = 2.844", "fov_deg = 5.0")
    with pytest.raises(ValueError):
        scene.build_scene(_write_toml(tmp_path, bad))


def test_validation_rejects_nonpositive_dims(tmp_path):
    bad = _GOOD_TOML.replace("width_px = 2048", "width_px = 0")
    with pytest.raises(ValueError):
        scene.build_scene(_write_toml(tmp_path, bad))


def test_validation_rejects_nonpositive_exposure(tmp_path):
    bad = _GOOD_TOML.replace("exposure_s = 2.0", "exposure_s = 0.0")
    with pytest.raises(ValueError):
        scene.build_scene(_write_toml(tmp_path, bad))


@pytest.mark.parametrize("limit", ["0.0", "-1.0", "30.0"])
def test_validation_rejects_insane_mag_limit(tmp_path, limit):
    bad = _GOOD_TOML.replace("gaia_mag_limit = 14.0", f"gaia_mag_limit = {limit}")
    with pytest.raises(ValueError):
        scene.build_scene(_write_toml(tmp_path, bad))


def test_validation_rejects_nonpositive_pixel_scale(tmp_path):
    bad = _GOOD_TOML.replace("pixel_scale_arcsec = 5.0", "pixel_scale_arcsec = 0.0")
    with pytest.raises(ValueError):
        scene.build_scene(_write_toml(tmp_path, bad))


# ---------------------------------------------------------------------------
# AC 1.2 — frozen TLE + Gaia CSV load OFFLINE
# ---------------------------------------------------------------------------

def test_committed_tle_fixture_loads_offline():
    cfg = scene.build_scene(str(DEFAULT_CONFIG))
    tle = scene.load_tle(scene.default_tle_path(cfg))
    # CelesTrak 3-line (0/1/2) or 2-line — loader returns the two orbital element lines.
    assert tle.line1.startswith("1 ")
    assert tle.line2.startswith("2 ")
    assert len(tle.line1) == 69
    assert len(tle.line2) == 69


def test_committed_gaia_fixture_loads_offline():
    cfg = scene.build_scene(str(DEFAULT_CONFIG))
    cat = scene.load_catalogue(scene.default_catalogue_path(cfg))
    assert {"ra", "dec", "phot_g_mean_mag"} <= set(cat.colnames)
    assert len(cat) > 300  # plausible star count for a ~2.8 deg field at mag<14
    # all stars are under the configured magnitude limit
    assert max(cat["phot_g_mean_mag"]) < cfg.gaia_mag_limit + 1e-6


def test_tle_loader_rejects_malformed_offline(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("<html>error</html>\n")
    with pytest.raises(ValueError):
        scene.load_tle(str(bad))
