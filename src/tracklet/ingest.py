"""ingest — real-frame counterpart to render (M1 Sprint 2).

Contract: ``ingest_external_image(image_path, meta, out_dir) -> IngestResult``.

render synthesizes a scene; ingest reads a GENUINE telescope FITS. Both are WRITERS that produce the
SAME solver-facing artifact — a 2-D ``float32`` ``image.fits`` with NO WCS header — so the M0
``solve_pointing`` / ``detect_streak`` run on the real frame UNCHANGED and BLIND. ingest is the second
clean-FITS writer; it is NOT a truth reader (it never deserializes truth — only ``score`` does; this
is pinned by the seal tests, which is why this module deliberately never names that JSON-read token).

The real-frame realities the synthetic path never hit are handled explicitly (Sprint-2 AC 2.1):
  * select the SCIENCE image HDU — data may not be in HDU 0 for multi-extension files; pick the HDU
    named in ``meta['frame']['science_hdu']`` (default: the first 2-D image HDU);
  * apply ``BSCALE``/``BZERO`` when casting integer data to float32 — this DDOTI frame is BITPIX 16 /
    BZERO 32768 (unsigned-16), so we let astropy scale it (``do_not_scale_image_data=False``);
  * canonicalise byte order to NATIVE (FITS stores big-endian on disk);
  * replace NON-FINITE pixels (NaN/Inf) with the frame median (a real detector has bad pixels);
  * PRESERVE pixel orientation (no flip/transpose) so the recovered WCS and the (Sprint-3) pointing
    truth describe the same array.

The WCS-free ``image.fits`` is written via the shared ``render.write_clean_fits`` helper (the seal in
ONE place). Satellite-truth (``truth.json`` via TLE -> skyfield) is assembled in Sprint 3, not here —
this module produces only the normalized solver image and returns the header pointing fields in-memory
for the downstream real-truth + report steps.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits

from tracklet.render import write_clean_fits


@dataclass(frozen=True)
class IngestResult:
    """Outcome of ingesting a real frame.

    Attributes
    ----------
    image : np.ndarray
        The normalized 2-D ``float32`` image plane (native byte order, finite, orientation-preserved)
        — exactly what the solver/detector consume.
    image_path : Path
        The written WCS-free ``image.fits`` (the solver-facing artifact).
    science_hdu : int
        Index of the HDU the science image was read from.
    header : fits.Header
        The SOURCE FITS header of the science HDU (pointing/timing truth lives here; read downstream
        in-memory by the Sprint-3 real-truth + report steps, NEVER fed into the blind solve).
    """

    image: np.ndarray
    image_path: Path
    science_hdu: int
    header: fits.Header


def _select_science_hdu(hdul: fits.HDUList, meta: dict) -> int:
    """Pick the science image HDU index: the one named in ``meta['frame']['science_hdu']`` if given,
    else the first HDU carrying a 2-D image. Fail loud if no 2-D image HDU exists."""
    named = meta.get("frame", {}).get("science_hdu")
    if named is not None:
        idx = int(named)
        data = hdul[idx].data
        if data is None or np.ndim(data) != 2:
            raise ValueError(
                f"meta science_hdu={idx} does not hold a 2-D image (ndim="
                f"{None if data is None else np.ndim(data)})"
            )
        return idx
    for idx, hdu in enumerate(hdul):
        if hdu.data is not None and np.ndim(hdu.data) == 2:
            return idx
    raise ValueError("no 2-D image HDU found in the FITS file")


def ingest_external_image(image_path: str, meta: dict, out_dir: str) -> IngestResult:
    """Read a real FITS frame -> normalized, WCS-stripped clean ``image.fits`` for the blind solver.

    Parameters
    ----------
    image_path : str
        Path to the real telescope FITS frame.
    meta : dict
        Parsed frame metadata (``meta.toml``). ``meta['frame']['science_hdu']`` selects the science
        HDU; the rest (timing/pointing/satellite) is consumed by the Sprint-3 real-truth step.
    out_dir : str
        Directory to write the clean ``image.fits`` into (created if absent).

    Returns
    -------
    IngestResult
        The normalized float32 image, the written clean-FITS path, the chosen HDU index, and the
        source science-HDU header (pointing/timing truth, read in-memory downstream — never by the
        blind solve).
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # do_not_scale_image_data=False -> astropy applies BSCALE/BZERO, recovering unsigned values.
    with fits.open(image_path, do_not_scale_image_data=False) as hdul:
        sci = _select_science_hdu(hdul, meta)
        data = hdul[sci].data
        header = hdul[sci].header.copy()
        # Cast to float32 in NATIVE byte order (FITS is big-endian on disk). astype(copy) detaches
        # from the closing HDUList's mmap and canonicalises endianness.
        image = np.asarray(data).astype(np.float32)

    image = np.ascontiguousarray(image)  # native-endian float32, contiguous

    # Replace non-finite pixels (NaN/Inf) with the frame median of the FINITE pixels. A real detector
    # has hot/dead/saturated pixels; left in, NaN poisons the background stats and Inf the source
    # extraction. The median is robust to the very bad pixels it is replacing.
    finite = np.isfinite(image)
    if not finite.all():
        fill = np.float32(np.median(image[finite]))
        image = np.where(finite, image, fill).astype(np.float32)

    # Orientation is preserved by construction: no flip/transpose is applied anywhere above.

    image_path_out = write_clean_fits(
        image,
        out / "image.fits",
        provenance={
            "BUNIT": ("adu", "detector counts (BSCALE/BZERO applied)"),
            "TRKLINGE": ("tracklet-ingest", "normalized real-frame (WCS-stripped)"),
        },
    )

    return IngestResult(
        image=image,
        image_path=image_path_out,
        science_hdu=int(sci),
        header=header,
    )
