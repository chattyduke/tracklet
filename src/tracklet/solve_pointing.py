"""solve_pointing — blind plate-solve (S3). The pipeline's pointing-recovery stage.

Contract: ``solve_pointing(image_path, scale_hint) -> SolveResult | SolveFailure``.

The seal in one sentence: this module sees ONLY the delivered, WCS-free ``image.fits`` and runs a
BLIND ``solve-field`` (no ``--ra/--dec`` seed). Even the scene's known pointing is never fed in, so
the recovered WCS is an INDEPENDENT measurement of where the camera looked — the non-circularity
guarantee that makes the downstream residual meaningful.

  * Reads NO truth. The signature takes ``(image_path, scale_hint)`` only — never a truth path,
    never the truth WCS. It imports neither ``score`` (the truth reader) nor ``render`` (the truth
    writer). (Pinned by the structural test in tests/test_solve_pointing.py, AC 3.3.)
  * Blind by default. We pass scale bounds (from the camera ``fov_deg``) so solve-field does not
    waste time scanning every scale, but NO position seed — solve-field searches the whole sky.
  * Honest failure. A no-solve (solve-field exits without a ``.wcs``) or a timeout RETURNS a typed
    ``SolveFailure`` with a reason string; it is NEVER raised and NEVER faked into a fabricated WCS.

Reuse (do not reinvent): ``subprocess`` drives the local ``solve-field`` binary (astrometry.net,
installed at S0); ``astropy.wcs.WCS`` parses the produced ``.wcs`` FITS header.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from astropy.wcs import WCS

# Path to the astrometry.net config that points at the S0-installed 4100-series indexes. solve-field
# uses this by default, but we pass it explicitly so the invocation is self-describing and portable
# (mirrors what the S0 smoke proved works). If absent, solve-field falls back to its own default.
_ASTROMETRY_CFG = "/opt/homebrew/etc/astrometry.cfg"

# Fractional half-width of the scale search window around the camera field-of-view. The blind solve
# still searches all of the sky; this only bounds the plate SCALE so solve-field skips index tiles
# at impossible scales (a speedup, not a position hint). +/-30% comfortably brackets the true scale.
_SCALE_MARGIN_FRAC = 0.30

# Wall-clock ceiling (seconds) for one solve-field invocation. A real golden-field solve completes
# well inside this; a pure-noise frame fails (no matchable asterism) quickly. A timeout is a
# legitimate no-solve -> SolveFailure, never an exception.
_SOLVE_TIMEOUT_S = 180.0


@dataclass(frozen=True)
class SolveResult:
    """A successful blind solve: the INDEPENDENTLY recovered pointing.

    ``wcs`` is the ``astropy.wcs.WCS`` parsed from solve-field's ``.wcs`` output — the recovered
    pointing, never read back from any header we wrote. ``solve_seconds`` is the wall-clock time the
    solve took; ``stdout_tail`` keeps the tail of solve-field's log for debugging / provenance.
    """

    wcs: WCS
    solve_seconds: float
    stdout_tail: str = ""


@dataclass(frozen=True)
class SolveFailure:
    """An HONEST no-solve. Returned (never raised), never a fabricated WCS.

    ``reason`` is a human-readable explanation (no .wcs produced / timeout / solve-field missing).
    ``solve_seconds`` is the wall-clock time spent before giving up; ``stdout_tail`` keeps the tail
    of solve-field's log so a failure can be diagnosed.
    """

    reason: str
    solve_seconds: float = 0.0
    stdout_tail: str = ""


class _BadScaleHint(ValueError):
    """A malformed scale_hint. Raised internally by ``_scale_bounds``; ``solve_pointing`` catches it
    and converts it to a typed ``SolveFailure`` so a caller-side mistake is an HONEST no-solve, not a
    stack trace. (Subclasses ValueError so the existing valid-hint contract is unchanged.)"""


def _scale_bounds(scale_hint) -> tuple[float, float]:
    """Derive (low, high) degwidth scale bounds from the scale hint (camera fov_deg).

    Accepts a mapping with ``fov_deg`` (or ``low``/``high`` directly) or a bare numeric fov. The
    bounds bracket the plate scale only; they carry NO sky position, so the solve stays blind.

    A malformed hint (a dict missing ``fov_deg``/``low``/``high``, or any non-numeric value) raises
    ``_BadScaleHint`` — never a bare ``KeyError``/``TypeError`` — so ``solve_pointing`` can turn it
    into a typed ``SolveFailure`` whose reason names the bad hint. VALID hints are byte-unchanged.
    """
    try:
        if isinstance(scale_hint, dict):
            if "low" in scale_hint and "high" in scale_hint:
                return float(scale_hint["low"]), float(scale_hint["high"])
            if "fov_deg" not in scale_hint:
                raise _BadScaleHint(
                    f"scale hint dict must carry 'fov_deg' or both 'low'/'high'; got keys "
                    f"{sorted(scale_hint)}"
                )
            fov = float(scale_hint["fov_deg"])
        else:
            fov = float(scale_hint)
    except _BadScaleHint:
        raise
    except (TypeError, ValueError) as exc:
        raise _BadScaleHint(f"scale hint is not numeric: {scale_hint!r} ({exc})") from exc
    return fov * (1.0 - _SCALE_MARGIN_FRAC), fov * (1.0 + _SCALE_MARGIN_FRAC)


def solve_pointing(image_path: str, scale_hint) -> "SolveResult | SolveFailure":
    """Blind plate-solve ``image_path`` -> recovered WCS, or an honest SolveFailure.

    Runs a headless, BLIND ``solve-field`` (no ``--ra/--dec`` seed) in a private temp work dir,
    bounding only the plate scale from ``scale_hint``. On success parses the produced ``.wcs`` with
    ``astropy.wcs.WCS``; on no-solve / timeout / missing solver returns a typed ``SolveFailure``.

    Parameters
    ----------
    image_path : str
        Path to the delivered FITS frame (WCS-free; the solver must recover pointing blindly).
    scale_hint : mapping | float
        Plate-scale hint, e.g. ``{"fov_deg": 2.844}`` (or explicit ``{"low": .., "high": ..}``, or a
        bare degwidth value). NOT a position hint — the solve remains blind.

    Returns
    -------
    SolveResult | SolveFailure
        ``SolveResult`` carrying the recovered ``astropy.wcs.WCS`` on a converged solve; otherwise a
        ``SolveFailure`` with a reason string. Never raises on a no-solve.
    """
    # Validate the scale hint FIRST so a malformed hint is an HONEST typed SolveFailure regardless of
    # whether solve-field is installed (deterministic + solver-independent — runs under -m "not solver").
    try:
        low, high = _scale_bounds(scale_hint)
    except _BadScaleHint as exc:
        return SolveFailure(reason=f"invalid scale hint: {exc}")

    solve_field = shutil.which("solve-field")
    if solve_field is None:
        return SolveFailure(reason="solve-field binary not found on PATH")

    src = Path(image_path)
    if not src.exists():
        return SolveFailure(reason=f"image not found: {image_path}")

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="tracklet_solve_") as work:
        work_dir = Path(work)
        # Copy the image into the private work dir so all of solve-field's siblings (.axy, .wcs,
        # .solved, ...) land there and are cleaned up with the temp dir — never beside the input.
        local_image = work_dir / src.name
        shutil.copy2(src, local_image)

        cmd = [
            solve_field,
            "--overwrite",
            "--no-plots",
            "--downsample", "2",
            "--scale-units", "degwidth",
            "--scale-low", f"{low:.4f}",
            "--scale-high", f"{high:.4f}",
            # BLIND: deliberately NO --ra / --dec / --radius seed.
            "--dir", str(work_dir),
            str(local_image),
        ]
        if Path(_ASTROMETRY_CFG).exists():
            cmd[1:1] = ["--config", _ASTROMETRY_CFG]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_SOLVE_TIMEOUT_S
            )
        except subprocess.TimeoutExpired:
            return SolveFailure(
                reason=f"solve-field timed out after {_SOLVE_TIMEOUT_S:.0f}s",
                solve_seconds=time.monotonic() - started,
            )

        elapsed = time.monotonic() - started
        stdout_tail = (proc.stdout or "")[-2000:]

        wcs_path = local_image.with_suffix(".wcs")
        if not wcs_path.exists():
            return SolveFailure(
                reason="solve-field produced no .wcs (no matchable asterism / no solve)",
                solve_seconds=elapsed,
                stdout_tail=stdout_tail,
            )

        try:
            # Read the .wcs header inside the with-block (the file vanishes with the temp dir);
            # WCS() copies the header into memory, so the returned object outlives the temp dir.
            wcs = WCS(str(wcs_path))
        except Exception as exc:  # noqa: BLE001 — a malformed .wcs is a no-solve, not a crash
            return SolveFailure(
                reason=f"produced .wcs could not be parsed by astropy: {exc}",
                solve_seconds=elapsed,
                stdout_tail=stdout_tail,
            )

        return SolveResult(wcs=wcs, solve_seconds=elapsed, stdout_tail=stdout_tail)
