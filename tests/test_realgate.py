"""M1 Sprint 4 — AC 4.6 plausibility gate (anti wrong-field-lock) unit tests.

The gate trusts a finite residual ONLY when the blind-recovered WCS center overlaps the independently
known pointing field: separation <= 0.5 * fov_deg. A wider miss is an HONEST typed failure (wrong
asterism), never a flattering residual. These tests pin the gate as a pure function on in-memory
centers + WCS — no solver, no truth read (non-solver).
"""
from __future__ import annotations

import numpy as np
import pytest
from astropy.wcs import WCS

from tracklet.realgate import check_field_overlap, wcs_center_radec


def _make_tan_wcs(center_ra, center_dec, naxis1, naxis2, scale_deg):
    """A minimal RA---TAN/DEC--TAN WCS centered on (center_ra, center_dec)."""
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crpix = [(naxis1 + 1) / 2.0, (naxis2 + 1) / 2.0]  # FITS 1-based center
    w.wcs.crval = [center_ra, center_dec]
    w.wcs.cdelt = [-scale_deg, scale_deg]  # negative CD1 so RA increases left
    return w


def test_wcs_center_radec_returns_central_pixel_world():
    """wcs_center_radec projects the (0-based) central pixel to world == the WCS crval here."""
    naxis1, naxis2 = 6144, 6220
    w = _make_tan_wcs(305.5565, -14.9640, naxis1, naxis2, 2.0 / 3600.0)
    ra, dec = wcs_center_radec(w, naxis1, naxis2)
    assert ra == pytest.approx(305.5565, abs=1e-3)
    assert dec == pytest.approx(-14.9640, abs=1e-3)


def test_overlap_passes_when_recovered_matches_expected_within_half_field():
    """A recovered center 0.3 deg from the expected center passes a 3.41-deg-FOV gate (tol 1.705)."""
    res = check_field_overlap(
        recovered_center_deg=(305.5565, -14.9640),
        expected_center_deg=(305.5565 + 0.3, -14.9640),  # ~0.29 deg off in RA at this dec
        fov_deg=3.41,
    )
    assert res.ok is True
    assert res.separation_deg < res.tolerance_deg
    assert res.tolerance_deg == pytest.approx(1.705)


def test_overlap_fails_on_wrong_field_lock_beyond_half_field():
    """A recovered center 2.25 deg from expected (the RAW recovered-vs-COMMANDED miss) FAILS the gate
    — this is exactly the wrong-asterism case the gate must reject as a typed failure, not a residual."""
    res = check_field_overlap(
        recovered_center_deg=(305.5565, -14.9640),  # blind-recovered C1 field
        expected_center_deg=(303.6068, -16.2040),   # commanded mount pointing (NO camera offset)
        fov_deg=3.41,
    )
    assert res.ok is False
    assert res.separation_deg == pytest.approx(2.25, abs=0.05)
    assert res.separation_deg > res.tolerance_deg


def test_overlap_uses_great_circle_separation_not_naive_radec():
    """Near the pole a naive RA difference massively overstates the angle; the gate must use the
    rigorous great-circle separation. Two points at Dec=85 with a 4-deg RA gap are < 0.5 deg apart."""
    res = check_field_overlap(
        recovered_center_deg=(10.0, 85.0),
        expected_center_deg=(14.0, 85.0),  # 4 deg of RA, but cos(85)*4 ~= 0.35 deg on sky
        fov_deg=3.41,
    )
    # naive |dRA| = 4 deg would FAIL; the true separation ~0.35 deg PASSES.
    assert res.separation_deg < 0.5
    assert res.ok is True


def test_overlap_handles_ra_wrap_at_zero_360():
    """Centers at RA 359.9 and RA 0.1 are 0.2 deg apart, not 359.8 — the wrap must not trip the gate."""
    res = check_field_overlap(
        recovered_center_deg=(359.9, 0.0),
        expected_center_deg=(0.1, 0.0),
        fov_deg=3.41,
    )
    assert res.separation_deg == pytest.approx(0.2, abs=1e-3)
    assert res.ok is True


def test_fov_must_be_positive():
    with pytest.raises(ValueError):
        check_field_overlap((10.0, 10.0), (10.0, 10.0), fov_deg=0.0)
    with pytest.raises(ValueError):
        check_field_overlap((10.0, 10.0), (10.0, 10.0), fov_deg=-3.41)
