"""S5 measure_position tests — AC 5.1 + the measure-side seal (all NON-solver).

measure_position is the pure pixel->sky lift: it takes a streak (anything exposing a sub-pixel
``.midpoint`` (x, y)) plus a WCS (the TRUE WCS in these tests; the blind-recovered WCS in the real
pipeline) and returns an astropy ``SkyCoord`` in ICRS via ``wcs.pixel_to_world``. It reads NO truth.

The non-circularity guarantee is structural (the signature is exactly ``(streak, wcs)``; the module
imports no truth loader, never names ``truth.json``, and never imports ``score``) — mirroring the
solve_pointing / detect_streak seals (tests/test_solve_pointing.py::test_module_does_not_reference_truth).

No solve-field, no network, no @solver: this whole file runs under ``pytest -m "not solver"``.
"""
from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u

from tracklet import measure_position as mp_module
from tracklet.measure_position import measure_position
from tracklet.render import build_truth_wcs
from tracklet.scene import build_scene

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"


@dataclass(frozen=True)
class _FakeStreak:
    """Minimal stand-in for StreakDetection: only the sub-pixel ``.midpoint`` is read by measure."""

    midpoint: tuple[float, float]


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


# ---------------------------------------------------------------------------
# AC 5.1 — pixel -> RA/Dec round-trip on the TRUE WCS (guards the origin/convention:
# the Y-flip / CD-sign class that S2's build_truth_wcs pins, exercised with origin=0).
# ---------------------------------------------------------------------------


def test_measure_lifts_midpoint_to_sky_matching_wcs_pixel_to_world(scene):
    """measure_position(streak, wcs) == wcs.pixel_to_world(x, y) to sub-arcsec.

    Uses an OFF-CENTER pixel (not crpix) so a swapped axis / wrong CD sign would show up.
    """
    wcs = build_truth_wcs(scene)
    x, y = 137.5, 902.25  # off-center, sub-pixel — not the reference pixel
    streak = _FakeStreak(midpoint=(x, y))

    measured = measure_position(streak, wcs)
    assert isinstance(measured, SkyCoord), f"expected a SkyCoord, got {type(measured)!r}"

    expected = wcs.pixel_to_world(x, y).icrs
    sep = measured.icrs.separation(expected).to(u.arcsec).value
    assert sep < 1e-3, f"measured sky pos differs from wcs.pixel_to_world by {sep:.6f}\""


def test_measure_round_trips_pixel_through_world_and_back(scene):
    """Project the measured SkyCoord back to pixels via wcs.world_to_pixel; recover (x, y) sub-pixel.

    A failed round-trip (off by the frame height, or x/y swapped) is exactly the origin/Y-flip bug
    this AC guards against.
    """
    wcs = build_truth_wcs(scene)
    x, y = 1487.0, 233.0  # off-center
    streak = _FakeStreak(midpoint=(x, y))

    measured = measure_position(streak, wcs)
    rx, ry = wcs.world_to_pixel(measured)
    assert np.hypot(float(rx) - x, float(ry) - y) < 1e-3, (
        f"round-trip pixel ({float(rx):.4f}, {float(ry):.4f}) != ({x}, {y})"
    )


def test_measure_returns_icrs_frame(scene):
    """The returned SkyCoord is in the ICRS frame (truth's frame; the comparison frame in score)."""
    wcs = build_truth_wcs(scene)
    measured = measure_position(_FakeStreak(midpoint=(640.0, 360.0)), wcs)
    assert measured.frame.name == "icrs", f"expected ICRS frame, got {measured.frame.name!r}"


# ---------------------------------------------------------------------------
# The measure-side seal — structural non-circularity (mirrors solve_pointing AC 3.3 /
# detect_streak AC 4.4). Pinned so the S7 seal already holds here.
# ---------------------------------------------------------------------------


def test_signature_takes_only_streak_and_wcs():
    params = list(inspect.signature(measure_position).parameters)
    assert params == ["streak", "wcs"], params


def test_module_does_not_reference_truth():
    """AST/source scan: measure_position imports no truth loader, never names truth.json, and does
    NOT import score. A measure step that reached for truth (or routed through score) would destroy
    the non-circularity argument; catch it structurally, not by trusting the runtime path.
    """
    source = Path(mp_module.__file__).read_text()
    assert "truth.json" not in source
    assert "_load_truth" not in source

    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            imported += [f"{mod}.{alias.name}" for alias in node.names]
    for forbidden in ("score", "tracklet.score", "render", "tracklet.render", "scene", "tracklet.scene"):
        assert not any(name == forbidden or name.endswith("." + forbidden) for name in imported), (
            f"measure_position must not import {forbidden}: imports={imported}"
        )
