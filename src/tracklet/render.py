"""render — synthetic scene renderer (S2). The ONLY writer of truth.

Contract: ``render_scene(scene, catalogue, tle, out_dir) -> RenderResult``.

render is the KEYSTONE of the pipeline and the FIRST + SOLE writer of sealed truth:

    scene -> render -> image.fits (CLEAN, no WCS header) + truth.json (SEALED)
                          -> [solve_pointing, detect_streak] -> measure_position -> score

The load-bearing seal (built to from the first commit, formally tested in S7):
  * ``image.fits`` is written WITHOUT any WCS header keywords (CRVAL/CD*/CTYPE/CRPIX/CDELT/PC*).
    The plate-solver must recover the pointing blindly — it never reads back a header we wrote.
  * ``render`` is the SOLE writer of ``truth.json``. No other module in the repo writes it; only
    ``score._load_truth`` reads it. The three solving modules never see a truth path.

Conventions (each pinned by a unit test in tests/test_render.py):
  * Synthetic ``RA---TAN`` / ``DEC--TAN`` WCS, ``crpix`` at the frame center (FITS 1-based),
    ``crval`` = scene center RA/Dec, NEGATIVE ``CD1_1`` so RA increases to the LEFT (east-left).
  * Projection uses ``wcs.wcs_world2pix(ra, dec, 0)`` (origin=0 for numpy arrays).
  * The image is indexed ``img[y, x]`` with FITS row 0 = bottom (so larger Dec -> larger y).
  * The satellite truth point is its ICRS RA/Dec at the exposure MIDPOINT (the streak midpoint);
    that is the point ``measure_position`` recovers and ``score`` compares against.

Pure-offline construction: consumes the frozen S1 fixtures (committed Gaia CSV + ISS TLE) and the
SceneConfig; touches no network and reads no truth.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

# --- rendering constants (deterministic; documented so the brightness model is auditable) ------
# Electrons collected from a magnitude-0 star over the exposure. The Gaia field here spans G ~ 3.8
# (very bright) to the G<14 limit. This zero-point must put a workable NUMBER of real stars clearly
# above the noise floor (sky ~200 e + read 5 e + Poisson ~sqrt(200) ~14 e/px), because the BLIND
# plate-solve (S3) builds its quad asterism from the brightest extracted sources and needs ~10-20
# genuine stars standing above noise. An earlier value of 1.0e5 left only the single brightest star
# clearly above noise (10th-brightest peaked ~11 e/px, ~1 sigma) — so the streak's bright fragments
# outranked the few detectable stars and the blind solve did not converge (S3 AC 3.1, the empirical
# gate). 1.0e6 puts the brightest ~tens of stars well above noise (brightest ~1400 e/px), so the
# genuine asterism dominates the source list and the blind solve locks on (recovered-vs-true ~0.6"
# at center). Still finite — no saturation modelling.
_FLUX_ZEROPOINT_E = 1.0e6
# Per-pixel sky background (electrons) — a flat diffuse floor so noise has something to act on and
# the frame is not a pure-black field of point sources.
_SKY_BACKGROUND_E = 200.0
# Per-pixel peak electrons (above sky) ALONG the streak ridge — the EXACT value at the trail center,
# rolling off transversely as a 1D Gaussian (see _render_streak; by construction the ridge peak ==
# this constant — no longitudinal-overlap amplification). The satellite is a bright fast-mover, so
# the trail sits at roughly the brightest-star level (brightest Gaia star here peaks ~1400 e/px above
# sky at _FLUX_ZEROPOINT_E=1e6) — bright enough to be an unambiguous linear feature for S4's Hough
# detector, but NOT orders of magnitude above the stars. The original render drove the ridge to
# ~1.7e5 e/px (~hundreds x the brightest star, and the constant misdescribed it as 8e3); solve-field's
# internal extractor (simplexy) then deblended the bright trail into ~a dozen collinear spurious point
# sources that, outranking every real star, filled the brightest-object quad search and STARVED the
# true-star asterism — the blind solve never converged (S3 AC 3.1, the empirical gate). Holding the
# ridge in the bright-star regime keeps the streak fragments OUT of the top of the source list so the
# blind plate-solve locks onto the real stars. (Mitigation #1 from the plan's Sprint-3 ladder; the
# root cause was an unphysical dynamic range, fixed here together with the too-faint star zero-point,
# so neither --downsample nor a pointing-hint nor ASTAP was needed.)
_STREAK_PEAK_E = 1.5e3
# Transverse 1-sigma width of the streak (pixels). A real trailed point source has the PSF width;
# reuse the star PSF sigma at render time (see _render_streak).


@dataclass(frozen=True)
class RenderResult:
    """Outcome of a render: the in-memory image, the truth payload, and where they were written.

    ``image`` is the final noisy float array indexed ``[y, x]`` (FITS row 0 = bottom). ``wcs`` is
    the TRUTH WCS (it is sealed into ``truth.json`` and NEVER written into ``image.fits``).
    """

    image: np.ndarray
    wcs: WCS
    truth: dict
    image_path: Path
    truth_path: Path


# ---------------------------------------------------------------------------
# Synthetic truth WCS
# ---------------------------------------------------------------------------


def build_truth_wcs(scene) -> WCS:
    """Build the synthetic TAN WCS that defines the scene's true pointing.

    RA---TAN / DEC--TAN, crpix at the (1-based) frame center, crval at the scene center, and a
    diagonal CD matrix with NEGATIVE CD1_1 (RA increases left) and positive CD2_2 (Dec increases
    up). This WCS is the TRUTH WCS: it is sealed into ``truth.json`` and is the frame the blind
    plate-solve must independently recover. It is NEVER written into ``image.fits``.
    """
    scale_deg = scene.pixel_scale_arcsec / 3600.0
    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    # FITS reference pixel is 1-based; the center of an N-pixel axis is (N+1)/2.
    wcs.wcs.crpix = [(scene.width_px + 1) / 2.0, (scene.height_px + 1) / 2.0]
    wcs.wcs.crval = [scene.center_ra_deg, scene.center_dec_deg]
    wcs.wcs.cd = np.array([[-scale_deg, 0.0], [0.0, scale_deg]])
    return wcs


# ---------------------------------------------------------------------------
# Satellite propagation (skyfield; ICRS astrometric — same frame as the solver's WCS)
# ---------------------------------------------------------------------------


def _exposure_times(scene) -> dict[str, dt.datetime]:
    """Exposure START / MIDPOINT / END as timezone-aware UTC datetimes.

    ``scene.utc`` is the exposure START; the midpoint (the scored-truth instant) is
    ``start + exposure_s/2``.
    """
    start = dt.datetime.fromisoformat(scene.utc.replace("Z", "+00:00"))
    return {
        "start": start,
        "mid": start + dt.timedelta(seconds=scene.exposure_s / 2.0),
        "end": start + dt.timedelta(seconds=scene.exposure_s),
    }


def _propagate_satellite(scene, tle) -> dict[str, tuple[float, float]]:
    """Propagate the satellite to exposure start/mid/end -> ICRS RA/Dec (deg).

    Uses ``(sat - wgs84.latlon(observer)).at(t).radec()`` with NO epoch arg, which returns ICRS
    astrometric RA/Dec — the SAME frame the blind solver's WCS reports, so truth and measured
    share a frame (the non-circularity argument is airtight).
    """
    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    sat = EarthSatellite(tle.line1, tle.line2, tle.name or "SAT", ts)
    obs = wgs84.latlon(
        scene.observer_lat_deg, scene.observer_lon_deg, elevation_m=scene.observer_elev_m
    )
    times = _exposure_times(scene)
    radec: dict[str, tuple[float, float]] = {}
    for label, when in times.items():
        t = ts.from_datetime(when)
        ra, dec, _ = (sat - obs).at(t).radec()
        radec[label] = (ra._degrees, dec.degrees)
    return radec


# ---------------------------------------------------------------------------
# Image construction (deterministic signal; single seeded noise draw)
# ---------------------------------------------------------------------------


def _render_stars(signal: np.ndarray, scene, catalogue, wcs: WCS) -> int:
    """Project Gaia stars and accumulate Gaussian PSFs into ``signal`` (electrons).

    flux ~ 10**(-0.4*mag) scaled by a zero-point; PSF sigma = ``scene.psf_sigma_px``. Indexing is
    ``signal[y, x]`` consistent with the FITS row-0-bottom convention. Returns the number of stars
    that landed in-frame (informational; used in the render summary).
    """
    ra = np.asarray(catalogue["ra"], dtype=float)
    dec = np.asarray(catalogue["dec"], dtype=float)
    mag = np.asarray(catalogue["phot_g_mean_mag"], dtype=float)

    x, y = wcs.wcs_world2pix(ra, dec, 0)
    sigma = float(scene.psf_sigma_px)
    half = int(np.ceil(5.0 * sigma))  # render PSF out to 5 sigma
    h, w = signal.shape

    # Only stars whose stamp can touch the frame matter.
    on = (x > -half) & (x < w + half) & (y > -half) & (y < h + half)
    flux = _FLUX_ZEROPOINT_E * 10.0 ** (-0.4 * mag)

    n_in_frame = 0
    inv_two_sig2 = 1.0 / (2.0 * sigma * sigma)
    for xi, yi, fi in zip(x[on], y[on], flux[on]):
        ix, iy = int(round(xi)), int(round(yi))
        x0, x1 = max(0, ix - half), min(w, ix + half + 1)
        y0, y1 = max(0, iy - half), min(h, iy + half + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        if 0 <= ix < w and 0 <= iy < h:
            n_in_frame += 1
        gx = np.arange(x0, x1) - xi
        gy = np.arange(y0, y1) - yi
        # Separable 2D Gaussian PSF, normalised to unit volume so total flux == fi.
        kern = (fi * inv_two_sig2 / np.pi) * np.outer(
            np.exp(-(gy * gy) * inv_two_sig2), np.exp(-(gx * gx) * inv_two_sig2)
        )
        signal[y0:y1, x0:x1] += kern
    return n_in_frame


def _render_streak(signal: np.ndarray, scene, px: dict[str, tuple[float, float]]) -> None:
    """Draw an antialiased satellite streak from the start pixel to the end pixel.

    The trail is a ridge of constant per-pixel peak ``_STREAK_PEAK_E`` (electrons, above sky) running
    along the start->end segment, with a 1D-Gaussian TRANSVERSE profile (sigma = ``scene.psf_sigma_px``)
    rolling off to either side. For every pixel in the streak's bounding region we compute its true
    perpendicular distance to the segment (clamped at the endpoints) and deposit
    ``_STREAK_PEAK_E * exp(-perp^2 / 2 sigma^2)`` ONCE — so the ridge peak is exactly ``_STREAK_PEAK_E``
    by construction (no longitudinal-overlap amplification), the constant means what it says, and the
    edge is smooth/sub-pixel. The streak peak is held in the same dynamic range as a bright star so
    solve-field's internal source extractor (simplexy) is not dominated by it (see the constant note).
    """
    sigma = float(scene.psf_sigma_px)
    (x0, y0) = px["start"]
    (x1, y1) = px["end"]
    h, w = signal.shape

    dx, dy = x1 - x0, y1 - y0
    length = float(np.hypot(dx, dy))
    if length == 0.0:
        return
    ux, uy = dx / length, dy / length  # unit vector along the streak
    half = int(np.ceil(5.0 * sigma))
    inv_two_sig2 = 1.0 / (2.0 * sigma * sigma)

    # Bounding box of the segment, padded by the transverse PSF reach, clipped to the frame.
    xlo = max(0, int(np.floor(min(x0, x1))) - half)
    xhi = min(w, int(np.ceil(max(x0, x1))) + half + 1)
    ylo = max(0, int(np.floor(min(y0, y1))) - half)
    yhi = min(h, int(np.ceil(max(y0, y1))) + half + 1)
    if xhi <= xlo or yhi <= ylo:
        return

    ys, xs = np.mgrid[ylo:yhi, xlo:xhi]
    # Project each pixel onto the segment: t = ((p-p0).u) clamped to [0, length]; the perpendicular
    # distance to the (clamped) segment then gives a true sub-pixel transverse falloff with rounded
    # ends, and the ridge along the segment sits at exactly _STREAK_PEAK_E.
    rx, ry = xs - x0, ys - y0
    t = np.clip(rx * ux + ry * uy, 0.0, length)
    perp_x = rx - t * ux
    perp_y = ry - t * uy
    perp2 = perp_x * perp_x + perp_y * perp_y
    signal[ylo:yhi, xlo:xhi] += _STREAK_PEAK_E * np.exp(-perp2 * inv_two_sig2)


def _build_signal(scene, catalogue, tle, wcs: WCS):
    """Build the deterministic, noise-free signal image (electrons) + the satellite geometry."""
    h, w = scene.height_px, scene.width_px
    signal = np.full((h, w), _SKY_BACKGROUND_E, dtype=np.float64)

    n_stars = _render_stars(signal, scene, catalogue, wcs)

    radec = _propagate_satellite(scene, tle)
    px: dict[str, tuple[float, float]] = {}
    for label, (ra, dec) in radec.items():
        x, y = wcs.wcs_world2pix(ra, dec, 0)
        px[label] = (float(x), float(y))
    _render_streak(signal, scene, px)
    return signal, radec, px, n_stars


def _add_noise(signal: np.ndarray, scene) -> np.ndarray:
    """Deterministic Poisson (shot) + Gaussian read noise via default_rng(seed).

    Single RNG seeded with ``scene.seed`` -> same seed gives a byte-identical array. The clipping
    keeps the Poisson mean non-negative; the read noise is additive Gaussian in electrons.
    """
    rng = np.random.default_rng(scene.seed)
    shot = rng.poisson(np.clip(signal, 0.0, None)).astype(np.float64)
    read = rng.normal(0.0, float(scene.read_noise_e), size=signal.shape)
    return shot + read


# ---------------------------------------------------------------------------
# Sealed truth
# ---------------------------------------------------------------------------


def _build_truth(scene, wcs: WCS, radec, px, catalogue_ref: str) -> dict:
    """Assemble the SEALED truth payload. render is the sole writer of this dict to disk."""
    times = _exposure_times(scene)

    def _iso(d: dt.datetime) -> str:
        return d.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    sat = {
        label: {"ra_deg": ra, "dec_deg": dec} for label, (ra, dec) in radec.items()
    }
    return {
        "wcs": {
            "ctype": list(wcs.wcs.ctype),
            "crpix": [float(v) for v in wcs.wcs.crpix],
            "crval": [float(v) for v in wcs.wcs.crval],
            "cd": [[float(v) for v in row] for row in wcs.wcs.cd],
        },
        "satellite": sat,
        # The scored truth point: satellite RA/Dec at the exposure MIDPOINT.
        "scored_truth": {"ra_deg": radec["mid"][0], "dec_deg": radec["mid"][1]},
        "satellite_px": {label: [px[label][0], px[label][1]] for label in px},
        "exposure": {
            "start_utc": _iso(times["start"]),
            "mid_utc": _iso(times["mid"]),
            "end_utc": _iso(times["end"]),
            "exposure_s": float(scene.exposure_s),
        },
        "seed": int(scene.seed),
        "catalogue_ref": catalogue_ref,
        "image_shape": [int(scene.height_px), int(scene.width_px)],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def render_scene(scene, catalogue, tle, out_dir) -> RenderResult:
    """Render the synthetic scene and write the CLEAN image + SEALED truth.

    Parameters
    ----------
    scene : SceneConfig
        The frozen scene parameters (camera, observer, exposure, noise, seed).
    catalogue : astropy Table
        The frozen Gaia catalogue (columns ``ra``, ``dec``, ``phot_g_mean_mag``).
    tle : tracklet.scene.TLE
        The frozen ISS two-line element set.
    out_dir : str | pathlib.Path
        Directory to write ``image.fits`` and ``truth.json`` into (created if absent).

    Returns
    -------
    RenderResult
        The in-memory image, the truth WCS, the truth dict, and the two output paths.

    Side effects
    ------------
    Writes ``<out_dir>/image.fits`` (NO WCS header — the seal) and ``<out_dir>/truth.json``
    (the SEALED truth — render is the sole writer). No network; reads no truth.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wcs = build_truth_wcs(scene)
    signal, radec, px, n_stars = _build_signal(scene, catalogue, tle, wcs)
    image = _add_noise(signal, scene)

    # The delivered image is float32 in NATIVE byte order. FITS stores big-endian on disk by
    # convention, so a consumer re-reading image.fits must canonicalise byte order before any
    # byte-level comparison; RenderResult.image is the canonical native-endian array, which keeps
    # the determinism hash (AC 2.1) stable and arch-consistent.
    image = np.ascontiguousarray(image.astype(np.float32))

    # --- write image.fits CLEAN: data only, NO WCS header keywords (the load-bearing seal) ------
    image_path = out_dir / "image.fits"
    hdu = fits.PrimaryHDU(data=image)
    # A minimal, WCS-free provenance note. Deliberately NO CRVAL/CD*/CTYPE/CRPIX/CDELT/PC*.
    hdu.header["BUNIT"] = ("electron", "approx detector electrons (synthetic)")
    hdu.header["TELESCOP"] = ("tracklet-synthetic", "synthetic-from-real-data scene")
    hdu.writeto(image_path, overwrite=True)

    # --- write truth.json SEALED: render is the SOLE writer -------------------------------------
    # Stamp the catalogue by its committed fixture FILENAME (not an absolute path) so truth.json
    # stays portable / machine-independent.
    from tracklet.scene import default_catalogue_path

    catalogue_ref = Path(default_catalogue_path(scene)).name
    truth = _build_truth(scene, wcs, radec, px, catalogue_ref=catalogue_ref)
    truth["n_stars_in_frame"] = int(n_stars)
    truth_path = out_dir / "truth.json"
    truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True))

    return RenderResult(
        image=image, wcs=wcs, truth=truth, image_path=image_path, truth_path=truth_path
    )
