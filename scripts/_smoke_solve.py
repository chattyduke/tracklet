#!/usr/bin/env python
"""S0 disposable smoke — confirm the installed 4100-series indexes actually solve (AC-0.5).

This is NOT pipeline code. It does NOT implement render.render_scene, does NOT write truth.json,
and does NOT touch score._load_truth — the sealed-truth Poka-Yoke is untouched. It exists only to
prove the plate-solver gate: project REAL Gaia stars (so the asterism matches the index catalogue)
into an xylist and blind-solve it. A blind solve that yields an astropy-loadable WCS == AC-0.5 pass.

Why an xylist (not a rendered image): it removes PSF/noise/source-extraction variability, so the
test exercises ONLY "do the installed indexes resolve a real-star geometry" — exactly AC-0.5's
intent. The real rendered-image solve is gated later in Sprint 3 against the golden frame.

Run:  .venv/bin/python scripts/_smoke_solve.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

# python.org macOS builds ship a stdlib `ssl` with no CA bundle until "Install Certificates.command"
# is run, so a live Gaia query fails cert verification. Point at certifi's (real, public) CA bundle
# so this works portably without disabling verification. (S1's fetch_fixtures will reuse this.)
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u

# A dense, bright field (near Orion) so a 2.8 deg frame has plenty of matchable bright stars.
CENTER_RA, CENTER_DEC = 83.8, -2.0
W = H = 2048
PIX_DEG = 5.0 / 3600.0  # 5 arcsec/px
FOV_DEG = W * PIX_DEG    # ~2.84 deg


def build_true_wcs() -> WCS:
    w = WCS(naxis=2)
    w.wcs.crpix = [W / 2, H / 2]
    w.wcs.cdelt = [-PIX_DEG, PIX_DEG]  # negative CD1_1 — RA increases to the left
    w.wcs.crval = [CENTER_RA, CENTER_DEC]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    return w


def get_gaia_stars():
    import time

    from astroquery.gaia import Gaia

    Gaia.ROW_LIMIT = 3000
    radius = 1.6  # deg — covers the frame half-diagonal (~2.0 deg) generously
    adql = (
        "SELECT ra, dec, phot_g_mean_mag FROM gaiadr3.gaia_source "
        f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{CENTER_RA},{CENTER_DEC},{radius})) "
        "AND phot_g_mean_mag < 12 ORDER BY phot_g_mean_mag ASC"
    )
    # The Gaia archive is documented-unstable (resets / timeouts under load) — retry transient errors
    # with backoff so the smoke (and a stranger reproducing) isn't defeated by archive flakiness.
    last = None
    for attempt in range(1, 4):
        try:
            r = Gaia.launch_job_async(adql).get_results()
            return np.asarray(r["ra"]), np.asarray(r["dec"]), np.asarray(r["phot_g_mean_mag"])
        except Exception as exc:  # noqa: BLE001 — transient archive errors are varied
            last = exc
            print(f"  Gaia query attempt {attempt}/3 failed ({type(exc).__name__}); retrying...")
            time.sleep(5 * attempt)
    raise RuntimeError(f"Gaia query failed after 3 attempts: {last}")


def main() -> int:
    w = build_true_wcs()
    ra, dec, mag = get_gaia_stars()
    x, y = w.wcs_world2pix(ra, dec, 0)
    keep = (x >= 0) & (x < W) & (y >= 0) & (y < H)
    x, y, mag = x[keep], y[keep], mag[keep]
    print(f"stars in frame: {len(x)} (mag<12, {FOV_DEG:.2f} deg field)")
    if len(x) < 20:
        print("SMOKE_FAIL: too few stars in frame to form quads")
        return 1

    flux = 10 ** (-0.4 * mag)
    order = np.argsort(-flux)
    x, y, flux = x[order], y[order], flux[order]

    with tempfile.TemporaryDirectory(prefix="tracklet_smoke_") as tmp:
        xyl = os.path.join(tmp, "field.xyls")
        fits.BinTableHDU.from_columns([
            fits.Column(name="X", format="E", array=x.astype("float32")),
            fits.Column(name="Y", format="E", array=y.astype("float32")),
            fits.Column(name="FLUX", format="E", array=flux.astype("float32")),
        ]).writeto(xyl, overwrite=True)

        cmd = [
            "solve-field", "--overwrite", "--no-plots",
            "--x-column", "X", "--y-column", "Y", "--sort-column", "FLUX",
            "--width", str(W), "--height", str(H),
            "--scale-units", "degwidth", "--scale-low", "2.0", "--scale-high", "3.6",
            xyl,
        ]
        print("blind-solving the real-star xylist ...")
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        wcs_path = os.path.join(tmp, "field.wcs")
        if not os.path.exists(wcs_path):
            sys.stderr.write(p.stdout[-2500:] + "\n" + p.stderr[-1500:] + "\n")
            print("SMOKE_FAIL: solve-field produced no .wcs")
            return 1
        rec = WCS(wcs_path)
        cra, cdec = rec.wcs_pix2world(W / 2, H / 2, 0)

    sep = SkyCoord(float(cra) * u.deg, float(cdec) * u.deg).separation(
        SkyCoord(CENTER_RA * u.deg, CENTER_DEC * u.deg)
    ).arcsec
    # A correct blind solve recovers the TRUE center to well within this; a spurious wrong-asterism
    # solve can still emit a loadable .wcs, so gate the pass on the offset (Poka-Yoke, not just "it loads").
    max_offset = 60.0
    if sep > max_offset:
        print(f'SMOKE_FAIL: WCS loaded but recovered-center offset {sep:.1f}" exceeds {max_offset:.0f}" '
              "(likely a spurious / wrong-asterism solve)")
        return 1
    print(f'SMOKE_PASS: blind solve OK; WCS loads; recovered-center offset {sep:.1f}" (< {max_offset:.0f}")')
    return 0


if __name__ == "__main__":
    sys.exit(main())
