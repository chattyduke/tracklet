"""S7 seal tests — the FORMAL sealed-truth / non-circularity gate (AC 7.1).

This is the single authoritative seal test for the milestone. It consolidates and formalises the
non-circularity argument the downstream modules already pin individually (test_solve_pointing /
test_detect_streak / test_measure_position) and adds the two integration-level guarantees the
per-module tests cannot give. The three pillars (the "3 seal tests" of AC 7.1):

  1. STATIC  — an AST/source scan proves the three SOLVING modules (solve_pointing, detect_streak,
     measure_position) name no sealed artifact (``truth.json``) and no truth loader (``_load_truth``),
     and import neither the truth READER (``score``) nor the truth WRITER (``render``)/``scene``. So
     they are structurally incapable of reading the answer they are graded against.
  2. RUNTIME — with ``score._load_truth`` monkeypatched to RAISE, the measurement path
     (detect_streak -> measure_position) still completes and only ``score`` fails. Positive proof
     that ``score`` is the SOLE truth reader: break the reader and the recovery is unaffected; only
     the grading step breaks.
  3. CLEAN-FITS — the delivered ``image.fits`` carries NO WCS keywords, re-asserted here at the
     integration boundary (render is the sole writer of the truth WCS; the solver recovers pointing
     blindly). Pinned at unit level by test_render.py::test_image_fits_has_no_wcs_keywords; the
     re-assertion makes this seal suite self-contained.

THE PIXEL CONVENTION (CD-sign / Y-flip / 0-vs-1 origin — the "1-px class") that the golden e2e's
10" gate is too loose to catch on its own is pinned INDEPENDENTLY and DETERMINISTICALLY, with no
dependence on solve-field, by the round-trip WCS tests that run on every ``pytest -m "not solver"``:
  * test_render.py::test_wcs_round_trip_subpixel_grid                 (world2pix<->pix2world, <1e-6 px)
  * test_render.py::test_wcs_ra_increases_left / ::test_wcs_dec_increases_up
  * test_render.py::test_wcs_center_maps_to_central_pixel
  * test_measure_position.py::test_measure_round_trips_pixel_through_world_and_back   (<1e-3 px, off-center)
  * test_measure_position.py::test_measure_lifts_midpoint_to_sky_matching_wcs_pixel_to_world
A 1-px convention regression fails those by ~1 px = 1e3..1e6x their tolerance — hard and
deterministic — so a convention bug cannot hide under the golden e2e's 10" gate.

All three pillars are NON-solver (no plate-solver needed) and run under ``pytest -m "not solver"``.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits

from tracklet import detect_streak as ds_module
from tracklet import measure_position as mp_module
from tracklet import score as score_module
from tracklet import solve_pointing as sp_module
from tracklet.detect_streak import StreakDetection, detect_streak
from tracklet.measure_position import measure_position
from tracklet.render import render_scene
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"

# The three SOLVING modules — structurally sealed away from truth (they never read the answer).
_SOLVING_MODULES = (sp_module, ds_module, mp_module)
# WCS keywords that MUST NOT appear in the clean image.fits header (mirrors test_render._WCS_KEYWORDS).
_WCS_KEYWORDS = ("CRVAL", "CD1_", "CD2_", "CTYPE", "CRPIX", "CDELT", "PC1_", "PC2_")


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


@pytest.fixture(scope="module")
def rendered(scene, tmp_path_factory):
    """Render the golden scene ONCE -> the delivered image.fits + sealed truth.json (render is the
    sole writer of both). Shared by the runtime + clean-FITS pillars. No solver needed."""
    out = tmp_path_factory.mktemp("seal")
    catalogue = load_catalogue(default_catalogue_path(scene))
    tle = load_tle(default_tle_path(scene))
    return render_scene(scene, catalogue, tle, out)


def _imported_names(module) -> list[str]:
    """Every module name imported by ``module`` (both ``import x`` and ``from x import y`` forms)."""
    tree = ast.parse(Path(module.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names.append(mod)
            names += [f"{mod}.{alias.name}" for alias in node.names]
    return names


# === Pillar 1: STATIC seal =====================================================================


@pytest.mark.parametrize("module", _SOLVING_MODULES, ids=lambda m: m.__name__.split(".")[-1])
def test_static_solving_module_never_names_the_sealed_artifact(module):
    """No solving module's source names the sealed artifact (``truth.json``) or its loader
    (``_load_truth``) — anywhere, code or docstring. (The modules discuss 'truth' in prose; the
    sealed ARTIFACT name and the LOADER name are what would betray an actual read.)"""
    source = Path(module.__file__).read_text()
    assert "truth.json" not in source, f"{module.__name__} names the sealed artifact 'truth.json'"
    assert "_load_truth" not in source, f"{module.__name__} references the truth loader '_load_truth'"


@pytest.mark.parametrize("module", _SOLVING_MODULES, ids=lambda m: m.__name__.split(".")[-1])
def test_static_solving_module_does_not_import_truth_reader_or_writer(module):
    """No solving module imports the truth READER (``score``) or the truth WRITER (``render``) — nor
    ``scene`` — so it is structurally incapable of reaching the sealed answer. This consolidates (and
    is strictly tighter than) the per-module seals in test_solve_pointing / test_detect_streak /
    test_measure_position."""
    imported = _imported_names(module)
    for forbidden in (
        "score", "tracklet.score", "render", "tracklet.render", "scene", "tracklet.scene"
    ):
        assert not any(
            name == forbidden or name.endswith("." + forbidden) for name in imported
        ), f"{module.__name__} must not import {forbidden}: imports={imported}"


# === Pillar 2: RUNTIME seal ====================================================================


def test_runtime_breaking_the_truth_reader_breaks_only_score(rendered, monkeypatch):
    """Monkeypatch ``score._load_truth`` to RAISE; the measurement path (detect_streak ->
    measure_position) still completes and only ``score`` fails — positive proof that ``score`` is
    the SOLE truth reader and the recovery never depends on the sealed answer.

    solve_pointing is omitted here only because it shells out to the real solver (it is @solver);
    its truth-independence is proven structurally above (it imports no truth loader and is
    subprocess-driven) and exercised end-to-end by the @solver golden e2e. The measurement path is
    the part that runs truth-adjacent Python in-process, so it is what this runtime probe exercises.
    """
    sentinel = "sealed truth reader deliberately broken by the seal test"

    def _boom(_truth_path):
        raise RuntimeError(sentinel)

    monkeypatch.setattr(score_module, "_load_truth", _boom)

    # The measurement path completes despite the broken truth reader. measure_position is
    # WCS-agnostic, so the TRUE WCS stands in for the recovered WCS here — this probe is about
    # truth-READING, not blind-solving (which the golden e2e covers end to end).
    detection = detect_streak(str(rendered.image_path))
    assert isinstance(detection, StreakDetection), f"detection must complete; got {detection!r}"
    measured = measure_position(detection, rendered.wcs)
    assert isinstance(measured, SkyCoord), "measurement must complete with the truth reader broken"

    # Only score — the sole truth reader — fails, and it fails THROUGH the broken loader.
    with pytest.raises(RuntimeError, match=sentinel):
        score_module.score(measured, str(rendered.truth_path))


# === Pillar 3: CLEAN-FITS seal (re-asserted at the integration boundary) =======================


def test_clean_fits_delivered_image_has_no_wcs_keywords(rendered):
    """The delivered image.fits carries NO WCS keywords — the solver must recover pointing blindly,
    never reading back a header we wrote. Unit-pinned by
    test_render.py::test_image_fits_has_no_wcs_keywords; re-asserted here so the seal suite is
    self-contained at the integration boundary."""
    with fits.open(rendered.image_path) as hdul:
        header = hdul[0].header
        keys = list(header.keys())
        for kw in _WCS_KEYWORDS:
            offenders = [k for k in keys if k.upper().startswith(kw)]
            assert not offenders, f"image.fits leaked WCS keyword(s) {offenders} (prefix {kw})"
        # Belt-and-braces: no WCS token anywhere in the raw header text (catches one smuggled into a
        # COMMENT/HISTORY card). This is the load-bearing seal.
        raw = header.tostring().upper()
        for kw in _WCS_KEYWORDS:
            assert kw not in raw, f"image.fits raw header contains WCS token {kw!r}"


# === M1 SEAL EXTENSION: the second writer (ingest) + the repo-wide json.load guard ==============
# M1 adds ingest, a SECOND writer of the sealed artifacts (real frames). It is seal-compatible iff:
#   (a) ingest writes a WCS-FREE image.fits (clean-FITS seal, symmetric to render)  -> below;
#   (b) ingest is structurally sealed away from truth like the solving modules
#       (it never names/imports the truth reader)                                   -> below;
#   (c) score remains the SOLE deserializer of truth: the json.load/json.loads token
#       appears ONLY in score.py across all of src/ (ingest is a json.dump writer)  -> below.


def _ingest_clean_image(tmp_path) -> Path:
    """Run ingest on a tiny unsigned-16 FITS carrying a (bogus) source WCS, returning the path to the
    WCS-stripped image.fits ingest wrote. The source WCS proves ingest STRIPS it, not merely that the
    source happened to be clean."""
    import numpy as np

    from tracklet.ingest import ingest_external_image

    src = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    raw = tmp_path / "src.fits"
    hdu = fits.PrimaryHDU(data=src)
    for k, v in {
        "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN",
        "CRVAL1": 303.6, "CRVAL2": -16.2, "CRPIX1": 1.0, "CRPIX2": 1.0,
        "CD1_1": -1e-4, "CD2_2": 1e-4,
    }.items():
        hdu.header[k] = v
    hdu.writeto(raw, overwrite=True)

    meta = {"frame": {"science_hdu": 0}, "solver": {"fov_deg": 3.41}}
    result = ingest_external_image(str(raw), meta, str(tmp_path / "out"))
    return result.image_path


def test_clean_fits_ingest_image_has_no_wcs_keywords(tmp_path):
    """Pillar 3 (clean-FITS), PARAMETRIZED OVER THE INGEST WRITER (AC 2.2): the image.fits ingest
    writes for the real path carries NO WCS keywords — even when the SOURCE frame had a header WCS, the
    normalized solver-facing output is WCS-stripped (the blind solve never reads back a header)."""
    image_path = _ingest_clean_image(tmp_path)
    with fits.open(image_path) as hdul:
        header = hdul[0].header
        keys = list(header.keys())
        for kw in _WCS_KEYWORDS:
            offenders = [k for k in keys if k.upper().startswith(kw)]
            assert not offenders, f"ingest image.fits leaked WCS keyword(s) {offenders} (prefix {kw})"
        raw = header.tostring().upper()
        for kw in _WCS_KEYWORDS:
            assert kw not in raw, f"ingest image.fits raw header contains WCS token {kw!r}"


def test_static_solving_module_does_not_import_ingest():
    """AC 2.3 — the forbidden-import list is EXTENDED over ingest: no solving module names or imports
    ingest. ingest is a writer, not part of the solving path, so a solving module reaching it would be
    a seal smell even though ingest itself reads no truth."""
    for module in _SOLVING_MODULES:
        imported = _imported_names(module)
        for forbidden in ("ingest", "tracklet.ingest"):
            assert not any(
                name == forbidden or name.endswith("." + forbidden) for name in imported
            ), f"{module.__name__} must not import {forbidden}: imports={imported}"
        source = Path(module.__file__).read_text()
        assert "ingest" not in source, f"{module.__name__} names 'ingest'"


def test_static_solving_module_does_not_import_realtruth():
    """M1 Sprint 3 — the forbidden-import list is EXTENDED over the THIRD writer, realtruth (it writes
    the real-frame truth.json from the TLE). Symmetric to ingest (AC 2.3): no solving module names or
    imports realtruth. realtruth is a truth WRITER (json.dump only); a solving module reaching it would
    be a seal smell even though realtruth itself never deserializes truth."""
    for module in _SOLVING_MODULES:
        imported = _imported_names(module)
        for forbidden in ("realtruth", "tracklet.realtruth"):
            assert not any(
                name == forbidden or name.endswith("." + forbidden) for name in imported
            ), f"{module.__name__} must not import {forbidden}: imports={imported}"
        source = Path(module.__file__).read_text()
        assert "realtruth" not in source, f"{module.__name__} names 'realtruth'"


def test_static_solving_module_does_not_import_tdm():
    """M2 Sprint 2 (AC 2.4) — the forbidden-import list is EXTENDED over the CCSDS TDM writer, tdm (a
    pure downstream-of-score artifact writer, symmetric to report). No solving module names or imports
    tdm. tdm is a DOWNSTREAM WRITER (text-formats the measured RA/Dec + epoch; never deserializes
    truth — auto-covered by the repo-wide json.load guard); a solving module reaching it would be a
    seal smell — the solving leaves must stay structurally isolated from every output writer.

    This guard BITES: adding ``import tracklet.tdm`` (or naming ``tdm`` in source) inside any of
    solve_pointing / detect_streak / measure_position fails it immediately."""
    for module in _SOLVING_MODULES:
        imported = _imported_names(module)
        for forbidden in ("tdm", "tracklet.tdm"):
            assert not any(
                name == forbidden or name.endswith("." + forbidden) for name in imported
            ), f"{module.__name__} must not import {forbidden}: imports={imported}"
        source = Path(module.__file__).read_text()
        assert "tdm" not in source, f"{module.__name__} names 'tdm'"


# --- The repo-wide json.load guard (AC 2.4) ----------------------------------------------------
# score is the SOLE truth DESERIALIZER. We prove it across ALL of src/ by an AST scan for the
# json.load / json.loads attribute-call token SPECIFICALLY — NOT a bare `load` substring, which would
# false-positive on skyfield's load.timescale() (render.py) and astropy fits/Table reads. ingest uses
# astropy + (in Sprint 3) json.dump, never json.load, so this guard catches a future regression that
# tried to make ingest or report read truth.json directly.

_SRC = _REPO / "src" / "tracklet"


def _module_deserializes_json(tree: ast.AST) -> bool:
    """True iff the module's AST contains a JSON deserialization call, ALIAS-RESISTANT:

      * any ``<name>.load(...)`` / ``<name>.loads(...)`` where ``<name>`` is bound to the stdlib
        ``json`` module (via ``import json`` OR ``import json as <name>``) — so an aliased
        ``import json as _j; _j.loads(...)`` does NOT slip past; and
      * a direct ``from json import load/loads`` bringing the deserializer into the namespace.

    Crucially it does NOT match ``load.<attr>(...)`` where ``load`` is skyfield's loader
    (``from skyfield.api import load`` -> ``load.timescale()``) or any astropy read — only names
    actually bound to the ``json`` module count, so the legitimate non-truth reads never false-positive.
    """
    json_module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "json":
                    json_module_aliases.add(alias.asname or "json")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "json" and any(
                a.name in ("load", "loads") for a in node.names
            ):
                return True  # `from json import load/loads` — the deserializer is in scope

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("load", "loads")
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in json_module_aliases
        ):
            return True
    return False


def _json_read_call_modules() -> list[str]:
    """Every src/tracklet/*.py whose AST deserializes JSON (alias-resistant; see helper)."""
    return [py.name for py in sorted(_SRC.glob("*.py")) if _module_deserializes_json(ast.parse(py.read_text()))]


def test_json_load_only_in_score_across_src():
    """AC 2.4 — the ``json.load``/``json.loads`` token appears in EXACTLY one module across src/:
    score.py (the sole truth reader). Any other module deserializing JSON-truth would break the
    non-circularity seal. Matched at the AST level (attribute call ``json.load``/``json.loads``), so
    skyfield ``load.timescale()`` and astropy reads do not false-positive."""
    offenders = _json_read_call_modules()
    assert offenders == ["score.py"], (
        f"json.load/json.loads must appear only in score.py across src/; found in {offenders}"
    )
