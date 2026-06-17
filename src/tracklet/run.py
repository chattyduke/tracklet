"""run — the ONE-command orchestrator + CLI (S6).

Wires the whole pipeline behind ``python -m tracklet.run [--config PATH] [--out DIR]``:

    build_scene -> render_scene -> [solve_pointing(BLIND), detect_streak]
        -> measure_position(RECOVERED wcs) -> score(truth_path) -> residual.txt + report

HONEST FAILURE is the load-bearing contract. A typed ``SolveFailure`` / ``DetectFailure`` surfaces as
a labelled message + a NON-ZERO exit code + NO residual.txt — never a stack trace and never a
fabricated residual. On success: write the finite residual, print it + the PASS/FAIL verdict, write
the report, and return 0.

The seal: run never reads the sealed answer itself. It hands ``score`` the answer PATH (score is the
sole reader) and uses the BLIND-recovered WCS — never the true WCS — for the measurement. (Pinned by
tests/test_run.py.)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Module-level imports so tests can monkeypatch tracklet.run.{solve_pointing,detect_streak}.
from tracklet.detect_streak import DetectFailure, detect_streak
from tracklet.measure_position import measure_position
from tracklet.render import render_scene
from tracklet.report import OverlayInputs, write_report
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)
from tracklet.score import score
from tracklet.solve_pointing import SolveFailure, solve_pointing

_REPO = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG = _REPO / "config" / "default_scene.toml"
_DEFAULT_OUT = _REPO / "out"


def _parse_args(argv: "list[str] | None") -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tracklet.run",
        description="Run the tracklet optical-SDA pipeline end to end on the synthetic scene.",
    )
    parser.add_argument(
        "--config", default=str(_DEFAULT_CONFIG), help="path to the scene TOML (default: %(default)s)"
    )
    parser.add_argument(
        "--out", default=str(_DEFAULT_OUT), help="output directory (default: %(default)s)"
    )
    return parser.parse_args(argv)


def main(argv: "list[str] | None" = None) -> int:
    """Run the whole pipeline once; return 0 on success, non-zero on an HONEST solve/detect failure."""
    from tracklet._env import assert_supported_python

    assert_supported_python()  # runtime guard: wrong Python minor fails loud before anything else

    args = _parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Scene + frozen real-data fixtures (offline; no network).
    scene = build_scene(args.config)
    catalogue = load_catalogue(default_catalogue_path(scene))
    tle = load_tle(default_tle_path(scene))

    # 2) Render -> the CLEAN (WCS-free) image.fits + the SEALED answer (render is the sole writer).
    rr = render_scene(scene, catalogue, tle, out_dir)

    # 3) BLIND plate-solve. A SolveFailure is HONEST: labelled message, no residual, non-zero exit.
    solve = solve_pointing(str(rr.image_path), {"fov_deg": scene.fov_deg})
    if isinstance(solve, SolveFailure):
        print(f"could not solve: {solve.reason}")
        return 2

    # 4) Detect the streak. A DetectFailure is equally HONEST.
    detection = detect_streak(str(rr.image_path))
    if isinstance(detection, DetectFailure):
        print(f"could not detect: {detection.reason}")
        return 3

    # 5) Measure through the BLIND-RECOVERED WCS (never the true WCS), then 6) score against the
    #    sealed answer PATH (score is the sole reader — run never opens the answer itself).
    measured = measure_position(detection, solve.wcs)
    result = score(measured, str(rr.truth_path))

    # 7) Write the FINITE residual (only ever written on a real, computed residual).
    (out_dir / "residual.txt").write_text(f"{result.residual_arcsec:.6f}\n")

    # 8) Surface the headline number + verdict, and write the human report.
    verdict = "PASS" if result.passed else "FAIL"
    print(
        f"residual: {result.residual_arcsec:.4f}\" "
        f"(threshold {result.threshold_arcsec}\") -> {verdict}"
    )
    overlay_inputs = OverlayInputs(
        image_path=rr.image_path, detection=detection, recovered_wcs=solve.wcs, scene=scene
    )
    write_report(result, overlay_inputs, str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
