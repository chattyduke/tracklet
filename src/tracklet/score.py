"""score — arcsecond residual vs the sealed truth (S5).

Contract: ``score(measured, truth_path) -> ScoreResult``. ``score._load_truth`` is the SOLE reader
of ``truth.json`` in the whole repo. The truth WRITERS are ``render`` (synthetic path), ``ingest``
(M1 real-frame clean image), and ``realtruth`` (M1 real-frame TLE→skyfield truth) — none of them
deserialize truth; every solving leaf (solve_pointing, detect_streak, measure_position) is
structurally sealed away from truth, so the non-circularity argument lives entirely here.

score reads the sealed ``scored_truth`` RA/Dec (the satellite position at the exposure MIDPOINT),
the measured position is the independent recovery, and the residual is the on-sky great-circle
separation in arcseconds via ``SkyCoord.separation``. The residual is ALWAYS the real separation —
never fabricated, never clamped. (The "no detection" honest-failure path is S6's run.py concern, not
score's: score always computes a true separation given a measured coord and a truth path.)
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from astropy.coordinates import SkyCoord
import astropy.units as u

# Pass/fail threshold on the on-sky residual. Error budget for the recovered satellite position is
# ~2-4" (RMS in quadrature: streak-midpoint centroiding sub-pixel to ~1px, the blind plate-solve's
# own astrometric fit ~1-2", and the ~1.4"/px pixel-scale quantization). 10" is a ~2-3x margin over
# that budget, so a stranger's independent solve+detect of the same frame cannot miss the gate by
# noise alone — yet it is far tighter than the half-degree a wrong-asterism solve would produce.
RESIDUAL_THRESHOLD_ARCSEC = 10.0


@dataclass(frozen=True)
class ScoreResult:
    """The scored record for one frame: the true on-sky residual and the pass/fail verdict.

    Attributes
    ----------
    residual_arcsec : float
        Great-circle separation between ``measured`` and the sealed truth, in arcseconds. ALWAYS the
        real separation.
    measured : SkyCoord
        The independently recovered sky position that was scored (ICRS).
    truth : SkyCoord
        The sealed truth sky position read from ``scored_truth`` (ICRS).
    threshold_arcsec : float
        The pass threshold applied (``RESIDUAL_THRESHOLD_ARCSEC``).
    passed : bool
        ``residual_arcsec < threshold_arcsec``.
    """

    residual_arcsec: float
    measured: SkyCoord
    truth: SkyCoord
    threshold_arcsec: float
    passed: bool


def _load_truth(truth_path: str) -> SkyCoord:
    """Read the sealed ``scored_truth`` RA/Dec -> an ICRS SkyCoord. THE sole truth reader.

    Opens ``truth.json`` and returns the satellite's exposure-MIDPOINT position
    (``truth["scored_truth"]["ra_deg"/"dec_deg"]``) as an ICRS coordinate — the point ``score``
    compares the measured recovery against.
    """
    with open(truth_path) as fh:
        truth = json.load(fh)
    scored = truth["scored_truth"]
    return SkyCoord(scored["ra_deg"] * u.deg, scored["dec_deg"] * u.deg, frame="icrs")


def score(measured, truth_path: str) -> ScoreResult:
    """Score a measured sky position against the sealed truth -> arcsecond residual + verdict.

    Parameters
    ----------
    measured : SkyCoord
        The independently recovered sky position (from measure_position over a recovered or true
        WCS). Coerced to ICRS for the comparison.
    truth_path : str
        Path to the sealed ``truth.json``; ``scored_truth`` is the only key read.

    Returns
    -------
    ScoreResult
        Carrying the real ``residual_arcsec`` and ``passed = residual < threshold``.
    """
    truth_coord = _load_truth(truth_path)
    # Native Python float (the separation .value is np.float64) so the scored record is a clean,
    # JSON-serialisable scalar and `passed` below is a genuine Python bool, not np.bool_.
    residual_arcsec = float(measured.icrs.separation(truth_coord).to(u.arcsec).value)
    return ScoreResult(
        residual_arcsec=residual_arcsec,
        measured=measured.icrs,
        truth=truth_coord,
        threshold_arcsec=RESIDUAL_THRESHOLD_ARCSEC,
        passed=residual_arcsec < RESIDUAL_THRESHOLD_ARCSEC,
    )
