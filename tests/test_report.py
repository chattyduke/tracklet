"""S6 report tests — AC 6.4 (artifacts well-formed) + the report-side seal. All NON-solver.

``write_report(score, overlay_inputs, out_dir)`` emits two human-facing artifacts:
  * ``report.md`` — scene summary, solve/detect status, the arcsec residual, threshold + PASS/FAIL,
    provenance, and a "what this PROVES / does NOT" section.
  * ``overlay.png`` — the image with the detected streak (endpoints + midpoint), the measured
    position marker, and a LABELLED TRUTH marker (truth pixel = score.truth projected through the
    RECOVERED wcs carried in overlay_inputs).

The report-side seal: report reads truth ONLY via ``score.truth`` (the SkyCoord on the ScoreResult).
It MUST NOT open the sealed truth artifact and MUST NOT import ``score._load_truth``. AC 6.4 stays
non-solver by using the TRUE WCS (``build_truth_wcs(scene)``) in place of a blind solve, mirroring
S5 AC 5.3.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tracklet import report as report_module
from tracklet.report import OverlayInputs, write_report
from tracklet.detect_streak import detect_streak, StreakDetection
from tracklet.measure_position import measure_position
from tracklet.render import build_truth_wcs, render_scene
from tracklet.score import RESIDUAL_THRESHOLD_ARCSEC, score
from tracklet.scene import (
    build_scene,
    default_catalogue_path,
    default_tle_path,
    load_catalogue,
    load_tle,
)

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"

# PNG magic bytes — the 8-byte signature every valid PNG begins with.
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="module")
def scene():
    return build_scene(str(_CONFIG))


@pytest.fixture(scope="module")
def golden(scene, tmp_path_factory):
    """Render the golden scene ONCE -> delivered image.fits + sealed truth.json (shared idiom)."""
    out = tmp_path_factory.mktemp("golden_report")
    catalogue = load_catalogue(default_catalogue_path(scene))
    tle = load_tle(default_tle_path(scene))
    return render_scene(scene, catalogue, tle, out)


@pytest.fixture(scope="module")
def scored(scene, golden):
    """detect -> measure(TRUE WCS) -> score on the golden frame (NON-solver; mirrors S5 AC 5.3)."""
    detection = detect_streak(str(golden.image_path))
    assert isinstance(detection, StreakDetection), f"expected a StreakDetection, got {detection!r}"
    wcs = build_truth_wcs(scene)
    measured = measure_position(detection, wcs)
    result = score(measured, str(golden.truth_path))
    return result, detection, wcs


# ---------------------------------------------------------------------------
# AC 6.4 — report.md carries the residual + PASS/FAIL + provenance; overlay.png is a valid PNG.
# ---------------------------------------------------------------------------


def test_report_md_has_residual_passfail_and_provenance(tmp_path, scene, golden, scored):
    result, detection, wcs = scored
    out = tmp_path / "out"
    out.mkdir()

    overlay_inputs = OverlayInputs(
        image_path=golden.image_path, detection=detection, recovered_wcs=wcs, scene=scene
    )
    write_report(result, overlay_inputs, str(out))

    report_md = out / "report.md"
    assert report_md.exists(), "write_report must write report.md"
    text = report_md.read_text()

    # The residual value (arcsec) must appear.
    assert f"{result.residual_arcsec:.4f}" in text or f"{result.residual_arcsec:.2f}" in text, (
        f"report.md must state the residual {result.residual_arcsec}\"; got:\n{text}"
    )
    # The PASS/FAIL verdict must appear.
    verdict = "PASS" if result.passed else "FAIL"
    assert verdict in text, f"report.md must state the {verdict} verdict; got:\n{text}"
    assert str(RESIDUAL_THRESHOLD_ARCSEC) in text, "report.md must state the threshold"

    # Provenance: the satellite, the TLE/Gaia fixtures, the solver index series, the Python version.
    assert scene.satellite_name in text, "provenance must name the satellite"
    assert "ISS" in text
    lower = text.lower()
    assert "gaia" in lower, "provenance must mention the Gaia catalogue"
    assert "tle" in lower, "provenance must mention the TLE source"
    assert "4100" in text, "provenance must name the astrometry.net 4100 index series"
    import sys

    assert sys.version.split()[0] in text, "provenance must stamp the running Python version"

    # The honest 'what this proves / does NOT' framing must be present.
    assert "synthetic" in lower, "report.md must state the result is synthetic-from-real-data"
    assert ("does not" in lower) or ("not a real" in lower), (
        "report.md must include the 'what this does NOT prove' honesty section"
    )


def test_overlay_png_is_a_valid_png(tmp_path, scene, golden, scored):
    result, detection, wcs = scored
    out = tmp_path / "out"
    out.mkdir()

    overlay_inputs = OverlayInputs(
        image_path=golden.image_path, detection=detection, recovered_wcs=wcs, scene=scene
    )
    write_report(result, overlay_inputs, str(out))

    overlay_png = out / "overlay.png"
    assert overlay_png.exists(), "write_report must write overlay.png"
    head = overlay_png.read_bytes()[:8]
    assert head == _PNG_MAGIC, f"overlay.png must be a valid PNG (magic bytes); got {head!r}"


# ---------------------------------------------------------------------------
# The report-side seal — report reads truth ONLY via score.truth; it never opens the sealed truth
# artifact and never calls the truth loader.
# ---------------------------------------------------------------------------


def test_report_does_not_open_truth_directly():
    """AST/source scan: report.py never parses JSON, never names truth.json, never calls _load_truth.

    report's only truth source is the SkyCoord ``score.truth`` already on the ScoreResult — if it
    opened the sealed truth itself it would become a second truth reader and break the seal.
    """
    source = Path(report_module.__file__).read_text()
    assert "json.load" not in source, "report.py must not parse JSON"
    assert "_load_truth" not in source, "report.py must not call score._load_truth"
    assert "truth.json" not in source, "report.py must not name the sealed-truth artifact"

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            src = ast.get_source_segment(source, node) or ""
            assert "truth" not in src.lower(), f"report.py must not open a truth file: {src!r}"


def test_overlay_inputs_carries_no_truth_path():
    """OverlayInputs must NOT carry a truth path that report could open — truth comes via score.truth."""
    fields = set(OverlayInputs.__dataclass_fields__)
    assert "truth_path" not in fields, "OverlayInputs must not carry a truth path"
    assert not any("truth" in f for f in fields), (
        f"OverlayInputs must not carry any truth-bearing field; got {fields}"
    )
