"""S6 run tests — the ONE-command orchestrator (ACs 6.1, 6.2, 6.3 + determinism + the run-side seal).

``run.main([...]) -> int`` wires the whole pipeline behind one command:

    build_scene -> render_scene -> [solve_pointing(BLIND), detect_streak]
        -> measure_position(RECOVERED wcs) -> score(truth_path) -> residual.txt + report

HONEST FAILURE is the load-bearing contract: a typed SolveFailure / DetectFailure must surface as a
labelled message + a NON-ZERO exit + NO residual.txt + NO fabricated residual — never a stack trace
and never a fake number.

  * AC 6.1 (@solver) — the FIRST full-pipeline BLIND-solve residual: a real ``solve-field`` run on
    the golden scene, exit 0, all three artifacts present, residual.txt a finite float (~2-4").
  * AC 6.2 (non-solver) — solve-failure honest: monkeypatch run's solve_pointing -> SolveFailure;
    non-zero exit, "could not solve" printed, NO residual.txt.
  * AC 6.3 (non-solver) — detect-failure honest: monkeypatch run's detect_streak -> DetectFailure;
    non-zero exit, "could not detect" printed, NO residual.txt.
  * Determinism (@solver) — two full runs on the golden scene give an identical image.fits sha AND
    an identical residual.txt.
  * Run-side seal (non-solver) — run.py never opens the sealed truth itself (score is the sole
    reader); structural grep/AST check.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from tracklet import run as run_module
from tracklet.run import main
from tracklet.solve_pointing import SolveFailure
from tracklet.detect_streak import DetectFailure

_REPO = Path(__file__).resolve().parent.parent
_CONFIG = _REPO / "config" / "default_scene.toml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# AC 6.1 (@solver) — the FIRST full-pipeline BLIND-solve residual.
# ---------------------------------------------------------------------------


@pytest.mark.solver
def test_full_pipeline_blind_solve_writes_artifacts_and_finite_residual(tmp_path, capsys):
    out = tmp_path / "out"
    rc = main(["--out", str(out)])

    captured = capsys.readouterr()
    assert rc == 0, f"full blind-solve pipeline must exit 0; got {rc}. stdout:\n{captured.out}"

    residual_txt = out / "residual.txt"
    overlay_png = out / "overlay.png"
    report_md = out / "report.md"
    assert residual_txt.exists(), "residual.txt must be written on a successful run"
    assert overlay_png.exists(), "overlay.png must be written on a successful run"
    assert report_md.exists(), "report.md must be written on a successful run"

    residual = float(residual_txt.read_text().strip())
    import math

    assert math.isfinite(residual), f"residual.txt must parse to a finite float; got {residual!r}"
    # The headline blind-solve number — surfaced so the human sees the real result.
    print(f"\n[AC 6.1] FULL-PIPELINE BLIND-SOLVE RESIDUAL = {residual:.4f}\" "
          f"(threshold 10.0\")")
    # Sanity band: a genuine blind solve+detect on this golden frame lands a few arcsec.
    assert 0.0 < residual < 10.0, (
        f"blind-solve residual {residual:.4f}\" is outside the expected pass band"
    )


@pytest.mark.solver
def test_full_pipeline_is_deterministic(tmp_path):
    """Two full blind-solve runs on the golden scene -> identical image.fits sha + identical residual."""
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    assert main(["--out", str(out_a)]) == 0
    assert main(["--out", str(out_b)]) == 0

    assert _sha256(out_a / "image.fits") == _sha256(out_b / "image.fits"), (
        "image.fits must be byte-identical across runs (render determinism)"
    )
    assert (out_a / "residual.txt").read_text() == (out_b / "residual.txt").read_text(), (
        "residual.txt must be identical across runs (deterministic end-to-end)"
    )


# ---------------------------------------------------------------------------
# AC 6.2 (non-solver) — solve-failure is HONEST: non-zero exit, labelled, NO residual.txt.
# ---------------------------------------------------------------------------


def test_solve_failure_is_honest_no_residual(tmp_path, capsys, monkeypatch):
    out = tmp_path / "out"

    def _fake_solve(image_path, scale_hint):
        return SolveFailure(reason="no matchable asterism (test injection)")

    monkeypatch.setattr(run_module, "solve_pointing", _fake_solve)

    rc = main(["--out", str(out)])
    captured = capsys.readouterr()

    assert rc != 0, "a SolveFailure must surface as a NON-ZERO exit code"
    assert "could not solve" in captured.out.lower(), (
        f"solve failure must print a labelled 'could not solve' message; stdout:\n{captured.out}"
    )
    assert "no matchable asterism (test injection)" in captured.out, (
        "the SolveFailure reason must be surfaced to the user"
    )
    assert not (out / "residual.txt").exists(), (
        "NO residual.txt may be written on a solve failure (no fabricated residual)"
    )


# ---------------------------------------------------------------------------
# AC 6.3 (non-solver) — detect-failure is HONEST: non-zero exit, labelled, NO residual.txt.
# ---------------------------------------------------------------------------


def test_detect_failure_is_honest_no_residual(tmp_path, capsys, monkeypatch):
    out = tmp_path / "out"

    def _fake_detect(image_path):
        return DetectFailure(reason="no linear features (test injection)")

    monkeypatch.setattr(run_module, "detect_streak", _fake_detect)

    rc = main(["--out", str(out)])
    captured = capsys.readouterr()

    assert rc != 0, "a DetectFailure must surface as a NON-ZERO exit code"
    assert "could not detect" in captured.out.lower(), (
        f"detect failure must print a labelled 'could not detect' message; stdout:\n{captured.out}"
    )
    assert "no linear features (test injection)" in captured.out, (
        "the DetectFailure reason must be surfaced to the user"
    )
    assert not (out / "residual.txt").exists(), (
        "NO residual.txt may be written on a detect failure (no fabricated residual)"
    )


# ---------------------------------------------------------------------------
# run-side seal (non-solver) — run never opens the sealed truth; score is the sole reader.
# ---------------------------------------------------------------------------


def test_main_signature_is_argv_only():
    params = list(inspect.signature(main).parameters)
    assert params == ["argv"], params


def test_run_does_not_open_truth_directly():
    """AST/source scan: run.py never opens the sealed truth nor calls a json loader / _load_truth.

    run hands score the truth PATH (score is the sole reader) — if run opened truth.json itself it
    would become a second truth reader and break the single-reader seal. Catch it structurally.
    """
    source = Path(run_module.__file__).read_text()
    assert "json.load" not in source, "run.py must not parse JSON (score is the sole truth reader)"
    assert "_load_truth" not in source, "run.py must not call score._load_truth"
    # The literal sealed-truth artifact name must not appear in run.py source (docstring or code).
    assert "truth.json" not in source, "run.py must not name the sealed-truth artifact"

    tree = ast.parse(source)
    # No bare `open(...)` of a truth file — run writes residual.txt but never reads truth.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            # open() is allowed for writing residual.txt; just ensure it never targets a truth path.
            src = ast.get_source_segment(source, node) or ""
            assert "truth" not in src.lower(), f"run.py must not open a truth file: {src!r}"


def test_json_load_appears_only_in_score_across_src():
    """Repo-wide seal: an actual ``json.load(`` call exists ONLY in score.py across src/tracklet/.

    score._load_truth is the SOLE reader of the sealed truth; if any other module gained a
    ``json.load`` it would be a candidate second reader. (We match the call form ``json.load(`` so
    docstring mentions of the string 'json.load' don't count.)
    """
    src_dir = Path(run_module.__file__).resolve().parent
    offenders = {
        p.name
        for p in src_dir.glob("*.py")
        if "json.load(" in p.read_text() and p.name != "score.py"
    }
    assert offenders == set(), f"json.load() must appear only in score.py; also found in {offenders}"
