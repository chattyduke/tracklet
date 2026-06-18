"""M1 Sprint 2 — ingest: real FITS -> normalized, WCS-stripped clean image (seal-preserving).

ingest is the real-frame counterpart to render (the synthetic writer): it reads a genuine telescope
FITS and produces the SAME solver-facing artifact render does — a 2-D float32 ``image.fits`` with NO
WCS header — so the M0 ``solve_pointing`` / ``detect_streak`` run on it UNCHANGED. The real-frame
realities the synthetic path never hit are handled explicitly and pinned here:

  * the science image may not be in HDU 0 (multi-extension files) — select the first 2-D image HDU,
    or one named in ``meta``;
  * integer data with ``BSCALE``/``BZERO`` (this DDOTI frame is BITPIX 16 / BZERO 32768 = unsigned-16)
    must be scaled when cast to float32 — let astropy apply it (``do_not_scale_image_data=False``);
  * byte order canonicalised to native (FITS stores big-endian on disk);
  * non-finite pixels (NaN/Inf) replaced with the frame median (a real detector has bad pixels);
  * pixel orientation PRESERVED (no flip/transpose) so the recovered WCS and the (Sprint-3) header /
    pointing truth describe the same array.

Most ACs (2.1-2.4) are pinned on SMALL synthetic FITS fixtures built in-test to carry exactly those
real-frame quirks — no network, no multi-MB frame. AC 2.5 (the binding @solver de-risk: the
NORMALIZED image still blind-solves+detects) runs on the genuine committed-provenance frame and is
SKIPPED if the gitignored frame is absent (fetch via tests/fixtures/real/fetch.sh).
"""
from __future__ import annotations

import inspect
import tomllib
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from tracklet.ingest import IngestResult, ingest_external_image

_REPO = Path(__file__).resolve().parent.parent
_REAL = _REPO / "tests" / "fixtures" / "real"
_WCS_KEYWORDS = ("CRVAL", "CD1_", "CD2_", "CTYPE", "CRPIX", "CDELT", "PC1_", "PC2_")


# ---------------------------------------------------------------------------
# Small synthetic FITS fixtures carrying the real-frame quirks (no network).
# ---------------------------------------------------------------------------


def _write_unsigned16_fits(path: Path, data_u16: np.ndarray, *, extra_header=None) -> None:
    """Write a single-HDU unsigned-16 FITS the way a real detector does: BITPIX 16 + BZERO 32768.

    astropy emits an unsigned-int image as int16 on disk with ``BZERO=32768`` so that, read back with
    scaling applied, the original unsigned values are recovered — the exact BSCALE/BZERO reality the
    real DDOTI frame presents.
    """
    hdu = fits.PrimaryHDU(data=data_u16.astype(np.uint16))
    if extra_header:
        for k, v in extra_header.items():
            hdu.header[k] = v
    hdu.writeto(path, overwrite=True)


@pytest.fixture
def meta_hdu0():
    return {"frame": {"science_hdu": 0}, "solver": {"fov_deg": 3.41}}


# === AC 2.1 — normalization correctness ========================================================


def test_ac21_reads_real_fits_to_float32_with_bscale_bzero_applied(tmp_path, meta_hdu0):
    """The unsigned-16 frame (BZERO 32768) is recovered as the ORIGINAL unsigned values in float32,
    not the raw signed int16 on disk. This is the BSCALE/BZERO reality of the DDOTI frame."""
    # Values straddling 32768 so a missing BZERO would wrap them to negatives.
    src = np.array([[0, 32768, 65535], [100, 40000, 20000]], dtype=np.uint16)
    raw = tmp_path / "frame.fits"
    _write_unsigned16_fits(raw, src)

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    assert isinstance(result, IngestResult)
    assert result.image.dtype == np.float32
    # The original UNSIGNED values are recovered (BZERO applied), not signed-int16 wrap-around.
    np.testing.assert_array_equal(result.image, src.astype(np.float32))


def test_ac21_byte_order_is_native(tmp_path, meta_hdu0):
    """The delivered array is in NATIVE byte order (FITS stores big-endian on disk)."""
    src = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    raw = tmp_path / "frame.fits"
    _write_unsigned16_fits(raw, src)

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    # Native byte order: the array's dtype byteorder is '=' or matches the platform's.
    assert result.image.dtype.isnative, f"array not native-endian: {result.image.dtype.byteorder!r}"


def test_ac21_non_finite_pixels_replaced_with_frame_median(tmp_path, meta_hdu0):
    """NaN/Inf pixels (real detectors have them) are replaced with the frame median, not left to
    poison the solver/detector or the median itself."""
    # A float frame so we can inject NaN/Inf directly.
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    data[2, 2] = np.nan
    data[0, 0] = np.inf
    data[4, 4] = -np.inf
    raw = tmp_path / "frame.fits"
    fits.PrimaryHDU(data=data).writeto(raw, overwrite=True)

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    assert np.all(np.isfinite(result.image)), "non-finite pixels survived ingest"
    finite_src = data[np.isfinite(data)]
    expected_fill = float(np.median(finite_src))
    assert result.image[2, 2] == pytest.approx(expected_fill)
    assert result.image[0, 0] == pytest.approx(expected_fill)
    assert result.image[4, 4] == pytest.approx(expected_fill)


def test_ac21_orientation_preserved_no_flip_or_transpose(tmp_path, meta_hdu0):
    """Pixel orientation is preserved exactly (no flip/transpose): a distinctive asymmetric pattern
    comes through with the same [y, x] indexing it had on disk, so a recovered WCS and the pointing
    truth describe the SAME array."""
    src = np.zeros((4, 6), dtype=np.uint16)
    src[0, 0] = 10  # bottom-left in FITS row-0 indexing
    src[3, 5] = 20  # top-right
    src[1, 4] = 30  # an interior asymmetric mark
    raw = tmp_path / "frame.fits"
    _write_unsigned16_fits(raw, src)

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    assert result.image.shape == src.shape  # (4, 6) — not transposed to (6, 4)
    np.testing.assert_array_equal(result.image, src.astype(np.float32))


def test_ac21_selects_named_science_hdu_for_multi_extension(tmp_path):
    """For a multi-extension (MEF) file the science image is not in HDU 0; ingest selects the HDU named
    in ``meta`` (here 1), not the empty primary."""
    primary = fits.PrimaryHDU()  # no data (typical MEF primary)
    sci = fits.ImageHDU(data=np.array([[7, 8], [9, 10]], dtype=np.uint16))
    raw = tmp_path / "mef.fits"
    fits.HDUList([primary, sci]).writeto(raw, overwrite=True)

    meta_hdu1 = {"frame": {"science_hdu": 1}, "solver": {"fov_deg": 3.41}}
    result = ingest_external_image(str(raw), meta_hdu1, str(tmp_path / "out"))

    np.testing.assert_array_equal(
        result.image, np.array([[7, 8], [9, 10]], dtype=np.float32)
    )


# === AC 2.2 — clean WCS-free image.fits ========================================================


def test_ac22_written_image_fits_has_no_wcs_keywords(tmp_path, meta_hdu0):
    """ingest writes a solver-facing image.fits with NO WCS keywords — even if the SOURCE frame
    carried a header WCS, the normalized output is WCS-stripped (the seal: the blind solve must
    recover pointing, never read back a header)."""
    src = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    raw = tmp_path / "frame.fits"
    # Deliberately put a (bogus) WCS in the SOURCE header to prove ingest strips it.
    _write_unsigned16_fits(
        raw,
        src,
        extra_header={
            "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
            "CRVAL1": 303.6, "CRVAL2": -16.2, "CRPIX1": 1.0, "CRPIX2": 1.0,
            "CD1_1": -1e-4, "CD2_2": 1e-4,
        },
    )

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    with fits.open(result.image_path) as hdul:
        header = hdul[0].header
        keys = list(header.keys())
        for kw in _WCS_KEYWORDS:
            offenders = [k for k in keys if k.upper().startswith(kw)]
            assert not offenders, f"ingest image.fits leaked WCS keyword(s) {offenders}"
        raw_hdr = header.tostring().upper()
        for kw in _WCS_KEYWORDS:
            assert kw not in raw_hdr, f"ingest image.fits raw header contains WCS token {kw!r}"


def test_ac22_written_image_fits_round_trips_to_the_same_array(tmp_path, meta_hdu0):
    """The clean image.fits on disk reads back to the same float32 array ingest returned in-memory
    (so the solver/detector consume exactly what ingest normalized)."""
    src = np.array([[0, 32768, 65535], [100, 40000, 20000]], dtype=np.uint16)
    raw = tmp_path / "frame.fits"
    _write_unsigned16_fits(raw, src)

    result = ingest_external_image(str(raw), meta_hdu0, str(tmp_path / "out"))

    with fits.open(result.image_path) as hdul:
        on_disk = np.ascontiguousarray(hdul[0].data).astype(np.float32)
    np.testing.assert_array_equal(on_disk, result.image)


# === AC 2.3 / 2.4 — seal (read side): ingest never reads truth ================================


def test_ac24_ingest_contains_no_json_load():
    """ingest is a WRITER (json.dump + astropy), never a truth READER: no ``json.load`` token in its
    source. (The repo-wide 'json.load only in score.py' seal test in test_seal.py is the integration
    guard; this is the unit-level guard on the new module.)"""
    src = Path(inspect.getsourcefile(ingest_external_image)).read_text()
    assert "json.load" not in src, "ingest must not call json.load (it is a writer, not a truth reader)"


def test_ac23_ingest_signature_takes_no_truth_path():
    """ingest_external_image's signature is (image_path, meta, out_dir) — it never receives a truth
    path; truth assembly (TLE->skyfield) is Sprint 3 and lives behind score's sole reader."""
    params = list(inspect.signature(ingest_external_image).parameters)
    assert params == ["image_path", "meta", "out_dir"], params


# === AC 2.5 — the binding de-risk (@solver): the NORMALIZED image still solves+detects ==========

_REAL_FRAME = _REAL / "20221118T024706C1o.fits"


@pytest.mark.solver
@pytest.mark.skipif(
    not _REAL_FRAME.exists(),
    reason="real BW3 frame absent (gitignored *.fits); run tests/fixtures/real/fetch.sh to obtain it",
)
def test_ac25_ingested_normalized_image_still_blind_solves_and_detects(tmp_path):
    """THE binding confirmation of the provisional Sprint-1 lock: normalization (HDU-select, BSCALE/
    BZERO, byte order, non-finite fill) did NOT destroy solvability. Re-run the M0 ``solve_pointing``
    + ``detect_streak`` VERBATIM on the NORMALIZED ingest output (not just the raw candidate) and
    assert both return non-failure types. If this FAILS, the frame is rejected -> back to Sprint 1
    (never weaken the seal or the gate to pass it)."""
    from tracklet.detect_streak import DetectFailure, StreakDetection, detect_streak
    from tracklet.solve_pointing import SolveFailure, SolveResult, solve_pointing

    with open(_REAL / "meta.toml", "rb") as fh:
        meta = tomllib.load(fh)

    result = ingest_external_image(str(_REAL_FRAME), meta, str(tmp_path / "out"))

    fov_deg = float(meta["solver"]["fov_deg"])
    solve = solve_pointing(str(result.image_path), {"fov_deg": fov_deg})
    assert isinstance(solve, SolveResult), f"normalized image must blind-solve; got {solve!r}"
    assert not isinstance(solve, SolveFailure)

    detection = detect_streak(str(result.image_path))
    assert isinstance(detection, StreakDetection), (
        f"normalized image must detect the streak; got {detection!r}"
    )
    assert not isinstance(detection, DetectFailure)
