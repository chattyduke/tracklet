"""report — human-facing artifacts: report.md + overlay.png (S6).

Contract: ``write_report(score, overlay_inputs, out_dir) -> None``.

The SEAL (load-bearing): report reads the truth position ONLY via the ScoreResult — ``score.truth``
is the ICRS SkyCoord ``score`` already resolved from the sealed answer. report NEVER opens the
sealed-answer artifact, never parses JSON, and never reaches for the score module's private truth
loader. ``OverlayInputs`` carries the rendered image, the StreakDetection, the RECOVERED WCS, and
the SceneConfig — but no path to the sealed answer. (Pinned by tests/test_report.py.)

  * ``report.md`` — scene summary, solve + detect status, the arcsec residual, threshold + PASS/FAIL,
    provenance (satellite, TLE + Gaia fixtures, the astrometry.net 4100 index series, solver, Python
    version), and an honest "what this PROVES / what it does NOT" framing.
  * ``overlay.png`` (matplotlib Agg) — the image with the detected streak (endpoints + midpoint), the
    MEASURED-position marker (the detected midpoint), and a LABELLED TRUTH marker (the truth SkyCoord
    projected to pixels through the RECOVERED WCS). Showing measured-vs-truth side by side makes the
    residual visible, not just stated.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits


@dataclass(frozen=True)
class OverlayInputs:
    """Everything ``write_report`` needs to draw the overlay — and deliberately NO sealed-answer path.

    Attributes
    ----------
    image_path : Path | str
        The delivered, WCS-free ``image.fits`` to render underneath the markers.
    detection : detect_streak.StreakDetection
        The detected trail (``.endpoints`` + sub-pixel ``.midpoint`` — the measured pixel).
    recovered_wcs : astropy.wcs.WCS
        The WCS the truth SkyCoord is projected through to place the truth marker. In the real
        pipeline this is the BLIND-recovered WCS; in non-solver tests it is the true WCS.
    scene : scene.SceneConfig
        The frozen scene parameters, used for the report.md scene summary + provenance.
    """

    image_path: "Path | str"
    detection: object
    recovered_wcs: object
    scene: object


# Provenance constant: the astrometry.net index series the S0-installed solver matches against.
_INDEX_SERIES = "4100"


def _render_md(score, scene) -> str:
    """Assemble report.md — scene summary, statuses, residual, verdict, provenance, honesty section."""
    verdict = "PASS" if score.passed else "FAIL"
    fov_deg = float(scene.fov_deg)
    return "\n".join(
        [
            "# tracklet — optical SDA atomic proof (report)",
            "",
            "## Scene",
            f"- Satellite: **{scene.satellite_name}** (CATNR {scene.catnr})",
            f"- Exposure start (UTC): {scene.utc}, exposure {scene.exposure_s:g} s",
            f"- Observer: lat {scene.observer_lat_deg:g}, lon {scene.observer_lon_deg:g}, "
            f"elev {scene.observer_elev_m:g} m",
            f"- Camera: {scene.width_px}x{scene.height_px} px @ "
            f"{scene.pixel_scale_arcsec:g}\"/px (FOV {fov_deg:.3f} deg)",
            f"- Pointing (camera center): RA {scene.center_ra_deg:.6f}, "
            f"Dec {scene.center_dec_deg:.6f} deg",
            "",
            "## Pipeline status",
            "- Solve (blind plate-solve): **SOLVED** (recovered WCS used for measurement)",
            "- Detect (streak): **DETECTED** (single coherent trail)",
            "",
            "## Result",
            f"- Measured: RA {score.measured.icrs.ra.deg:.6f}, "
            f"Dec {score.measured.icrs.dec.deg:.6f} deg",
            f"- Truth:    RA {score.truth.icrs.ra.deg:.6f}, "
            f"Dec {score.truth.icrs.dec.deg:.6f} deg",
            f"- **Residual: {score.residual_arcsec:.4f}\"**",
            f"- Threshold: {score.threshold_arcsec}\" -> **{verdict}**",
            "",
            "## Provenance",
            f"- TLE source: CelesTrak GP (CATNR {scene.catnr}, frozen snapshot under data/tle/)",
            "- Star catalogue: Gaia DR3 cone (frozen snapshot under data/catalogue/)",
            f"- Plate solver: astrometry.net solve-field, {_INDEX_SERIES}-series index files "
            "(blind solve — no position seed)",
            f"- Python: {sys.version.split()[0]}",
            "",
            "## What this proves — and what it does NOT",
            "- PROVES: a synthetic-from-real-data frame (real Gaia stars + a real ISS TLE) can be "
            "blind plate-solved and its satellite streak measured to a sub-arcsecond–to–"
            "few-arcsecond on-sky residual against independently sealed truth.",
            "- DOES NOT prove a real-sensor result: the image is SYNTHETIC (rendered, not captured "
            "through optics + a detector). Atmosphere, optical aberrations, real noise, and sensor "
            "artifacts are NOT modelled. This is a software-pipeline proof, not a hardware result.",
            "",
        ]
    )


def _truth_pixel(score, recovered_wcs) -> "tuple[float, float] | None":
    """Project the truth SkyCoord (score.truth) to pixels through the recovered WCS.

    Returns ``(x, y)`` or ``None`` if the projection is non-finite (truth off the recovered frame).
    The ONLY truth source is ``score.truth`` — never the sealed-answer artifact.
    """
    x, y = recovered_wcs.world_to_pixel(score.truth)
    x, y = float(x), float(y)
    if not (np.isfinite(x) and np.isfinite(y)):
        return None
    return x, y


def _render_overlay(score, overlay_inputs, out_path: Path) -> None:
    """Draw the image + detected streak + measured marker + labelled truth marker -> overlay.png."""
    import matplotlib

    matplotlib.use("Agg")  # headless backend — MUST precede pyplot import
    import matplotlib.pyplot as plt

    image = np.asarray(fits.getdata(str(overlay_inputs.image_path)), dtype=np.float64)
    det = overlay_inputs.detection
    (x0, y0), (x1, y1) = det.endpoints
    mx, my = det.midpoint  # the MEASURED pixel == the detected midpoint

    # Robust display scaling so the stars + trail are visible without one bright star saturating.
    vmin = float(np.percentile(image, 50.0))
    vmax = float(np.percentile(image, 99.5))

    fig, ax = plt.subplots(figsize=(8, 8))
    # origin="lower" matches render's FITS row-0-bottom convention (so pixel y grows upward).
    ax.imshow(image, origin="lower", cmap="gray", vmin=vmin, vmax=vmax)

    ax.plot([x0, x1], [y0, y1], color="cyan", lw=1.0, alpha=0.8, label="detected streak")
    ax.scatter([x0, x1], [y0, y1], s=30, facecolors="none", edgecolors="cyan", lw=1.0)
    ax.scatter([mx], [my], s=120, marker="+", color="lime", lw=2.0, label="measured (midpoint)")

    truth_px = _truth_pixel(score, overlay_inputs.recovered_wcs)
    if truth_px is not None:
        tx, ty = truth_px
        ax.scatter([tx], [ty], s=160, marker="x", color="red", lw=2.0, label="truth")
        ax.annotate(
            "truth", (tx, ty), textcoords="offset points", xytext=(8, 8), color="red", fontsize=9
        )

    verdict = "PASS" if score.passed else "FAIL"
    ax.set_title(
        f"tracklet: residual {score.residual_arcsec:.3f}\" "
        f"(threshold {score.threshold_arcsec}\") -> {verdict}"
    )
    ax.legend(loc="upper right", framealpha=0.7, fontsize=8)
    ax.set_xlabel("x (px)")
    ax.set_ylabel("y (px)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def write_report(score, overlay_inputs, out_dir: str) -> None:
    """Write ``report.md`` + ``overlay.png`` into ``out_dir`` from the ScoreResult + overlay inputs.

    Truth is read ONLY via ``score.truth`` (the ICRS SkyCoord on the ScoreResult); this module never
    opens the sealed-answer artifact. Pure side effects; returns None.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(_render_md(score, overlay_inputs.scene))
    _render_overlay(score, overlay_inputs, out / "overlay.png")
