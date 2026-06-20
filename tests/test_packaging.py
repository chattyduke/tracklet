"""M2 Sprint 1 — packaging gate: tracklet is a real pip-installable package.

This test is the executable contract for "stranger can `pip install` tracklet and the CLI works".
It proves, WITHOUT touching the dev `.venv`:

  * AC 1.1 — `python -m build --no-isolation` produces BOTH a wheel and an sdist with no error, and
    the built version == `tracklet.__version__` == "0.1.2" (single source — pyproject is `dynamic`).
  * AC 1.2 — a fresh `pip install dist/*.whl` into a throwaway venv exposes a WORKING `tracklet`
    console command AND `python -m tracklet` (entry points wired). The full synthetic-scene
    end-to-end run through the installed CLI is the @solver half (needs solve-field) — kept out of
    the `-m "not solver"` gate but still asserted under `pytest -m solver`.
  * AC 1.3 — from the installed package, `importlib.metadata.version("tracklet") == "0.1.2"` and
    `import tracklet; tracklet.__version__ == "0.1.2"`.
  * AC 1.4 — `dependencies` carry lower bounds <= the locked versions; `pip install . -c
    requirements.lock` resolves with no conflict.

Design notes (Poka-Yoke):
  * The wheel is built `--no-isolation` against the dev-extra build backend (build/setuptools/wheel)
    so a clean machine never needs PyPI build-isolation. The dev `.venv` must therefore have the
    build backend installed first (`pip install -e ".[dev]"`).
  * Every install happens in a hermetic throwaway venv under pytest's tmp_path — the dev `.venv` is
    never mutated.
  * The build + the throwaway-venv installs are slow-ish (seconds), so they are module-scoped
    fixtures shared across the non-solver assertions.
"""
from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
import tomllib
import venv
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_EXPECTED_VERSION = "0.1.2"


def _bin(venv_dir: Path, name: str) -> Path:
    """Path to an executable inside a created venv (Scripts/ on Windows, bin/ elsewhere)."""
    sub = "Scripts" if os.name == "nt" else "bin"
    exe = name + (".exe" if os.name == "nt" else "")
    return venv_dir / sub / exe


def _run(cmd, **kw):
    """Run a command, capturing output; raise a readable error on non-zero exit."""
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"command failed ({proc.returncode}): {cmd}\n--- output ---\n{proc.stdout}"
        )
    return proc.stdout


@pytest.fixture(scope="module")
def built_dist(tmp_path_factory):
    """Build wheel + sdist into a clean dist dir via `python -m build --no-isolation` (AC 1.1).

    Uses the CURRENT interpreter (the dev venv) as the build backend host — so the dev venv must
    already have build/setuptools/wheel (the `.[dev]` extra). Output goes to a tmp dist dir, NOT the
    repo's dist/, so the test is hermetic and order-independent.
    """
    out = tmp_path_factory.mktemp("dist")
    try:
        import build  # noqa: F401
    except ModuleNotFoundError:
        pytest.fail(
            "the build backend is not installed in the dev venv; run "
            "`.venv/bin/pip install -e \".[dev]\"` first (S1 bootstrap precondition)"
        )
    _run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(out), str(_REPO)],
    )
    wheels = sorted(out.glob("*.whl"))
    sdists = sorted(out.glob("*.tar.gz"))
    assert wheels, f"no wheel produced in {out}: {list(out.iterdir())}"
    assert sdists, f"no sdist produced in {out}: {list(out.iterdir())}"
    return {"dir": out, "wheel": wheels[0], "sdist": sdists[0]}


@pytest.fixture(scope="module")
def installed_venv(tmp_path_factory, built_dist):
    """Create a throwaway venv and `pip install` the built WHEEL into it (AC 1.2/1.3).

    Hermetic: a fresh venv under tmp, the dev `.venv` is never touched. We install the wheel alone
    (its declared deps are already satisfied by the build host's resolver against the current index;
    in CI the lock-constrained install is exercised separately — AC 1.4 below).
    """
    venv_dir = tmp_path_factory.mktemp("install_venv") / "venv"
    venv.create(venv_dir, with_pip=True, clear=True)
    py = _bin(venv_dir, "python")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    _run([str(py), "-m", "pip", "install", str(built_dist["wheel"])])
    return venv_dir


# === AC 1.1 — build produces wheel + sdist; built version == single source =====================


def test_build_produces_wheel_and_sdist(built_dist):
    """AC 1.1 — both artifacts exist and carry the single-source version in their filename."""
    assert built_dist["wheel"].name.startswith(f"tracklet-{_EXPECTED_VERSION}-"), (
        f"wheel name {built_dist['wheel'].name!r} does not carry version {_EXPECTED_VERSION}"
    )
    assert built_dist["sdist"].name == f"tracklet-{_EXPECTED_VERSION}.tar.gz", (
        f"sdist name {built_dist['sdist'].name!r} != tracklet-{_EXPECTED_VERSION}.tar.gz"
    )


def test_single_source_version_is_0_1_2():
    """AC 1.1/1.3 — the ONE version source (`tracklet.__version__`) is 0.1.2."""
    import tracklet

    assert tracklet.__version__ == _EXPECTED_VERSION


def test_pyproject_version_is_dynamic_from_init():
    """AC 1.1 — pyproject declares the version `dynamic` and resolves it from `tracklet.__version__`
    (single source), so there is no second hardcoded version to drift."""
    pyproject = tomllib.loads((_REPO / "pyproject.toml").read_text())
    project = pyproject["project"]
    assert "version" not in project, "pyproject must NOT hardcode a static [project] version"
    assert project.get("dynamic") == ["version"], (
        f"[project] dynamic must be ['version']; got {project.get('dynamic')!r}"
    )
    dyn = pyproject["tool"]["setuptools"]["dynamic"]["version"]
    assert dyn == {"attr": "tracklet.__version__"}, (
        f"dynamic version must come from tracklet.__version__; got {dyn!r}"
    )


# === AC 1.2 — installed console command + python -m tracklet both work ==========================


def test_installed_console_command_exists_and_runs(installed_venv):
    """AC 1.2 — the `tracklet` console script is installed and runs (its --help exits 0). The full
    synthetic end-to-end run is the @solver half below; here we prove the entry point is wired."""
    tracklet_cmd = _bin(installed_venv, "tracklet")
    assert tracklet_cmd.exists(), f"console command not installed at {tracklet_cmd}"
    out = _run([str(tracklet_cmd), "--help"])
    assert "tracklet" in out.lower()


def test_installed_python_m_tracklet_runs(installed_venv):
    """AC 1.2 — `python -m tracklet --help` works from the installed package (the __main__ shim)."""
    py = _bin(installed_venv, "python")
    out = _run([str(py), "-m", "tracklet", "--help"])
    assert "tracklet" in out.lower()


# === AC 1.3 — version consistency from the installed package ====================================


def test_installed_metadata_and_import_version_match(installed_venv):
    """AC 1.3 — `importlib.metadata.version('tracklet')` == `tracklet.__version__` == 0.1.2 from
    INSIDE the throwaway install (not the source tree)."""
    py = _bin(installed_venv, "python")
    out = _run(
        [
            str(py),
            "-c",
            "import importlib.metadata as m, tracklet; "
            "print(m.version('tracklet')); print(tracklet.__version__)",
        ]
    )
    lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    assert lines[-2:] == [_EXPECTED_VERSION, _EXPECTED_VERSION], (
        f"installed metadata/import version mismatch: {lines[-2:]} != "
        f"[{_EXPECTED_VERSION}, {_EXPECTED_VERSION}]"
    )


# === AC 1.4 — dependency lower bounds resolve under the lockfile ================================


def test_dependency_lower_bounds_at_or_below_locked():
    """AC 1.4 — every pyproject dependency carries a lower bound, and that bound is <= the version
    pinned in requirements.lock (so the bounds can NEVER conflict with the exact-reproduce lock)."""
    pyproject = tomllib.loads((_REPO / "pyproject.toml").read_text())
    deps = pyproject["project"]["dependencies"]
    locked = _parse_lock_versions(_REPO / "requirements.lock")

    for spec in deps:
        name, lower = _parse_lower_bound(spec)
        assert lower is not None, f"dependency {spec!r} has no lower bound (>=)"
        key = name.lower().replace("_", "-")
        assert key in locked, f"dependency {name!r} not found in requirements.lock"
        assert _ver_tuple(lower) <= _ver_tuple(locked[key]), (
            f"{name} lower bound {lower} > locked {locked[key]} (would conflict with the lock)"
        )


def test_pip_install_with_lock_constraint_resolves(tmp_path):
    """AC 1.4 — `pip install . -c requirements.lock` resolves the locked set with no conflict.

    We run pip's resolver in `--dry-run` mode against a fresh throwaway venv so
    we exercise the REAL resolver (not just a version-string compare) without mutating the dev venv.
    The dependencies are already present in the dev venv's wheel cache, so this is offline-fast.
    """
    venv_dir = tmp_path / "lockcheck"
    venv.create(venv_dir, with_pip=True, clear=True)
    py = _bin(venv_dir, "python")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    # --dry-run proves the resolver finds a conflict-free set under the lock constraints without a
    # full (slow) install; a constraint/version conflict makes pip exit non-zero -> _run raises.
    _run(
        [
            str(py),
            "-m",
            "pip",
            "install",
            "--dry-run",
            "-c",
            str(_REPO / "requirements.lock"),
            str(_REPO),
        ]
    )


# === AC 1.2 (full e2e) — the installed CLI runs the synthetic scene end to end (@solver) =========


@pytest.mark.solver
def test_installed_wheel_cli_runs_synthetic_scene_end_to_end(installed_venv, tmp_path):
    """AC 1.2 full claim — the NON-EDITABLE WHEEL install's `tracklet` console command runs the
    synthetic scene end to end (blind solve -> detect -> measure -> score) and writes a residual.
    Needs solve-field + indexes (the @solver gate); excluded from `pytest -m "not solver"`.

    The synthetic scene reads its committed Gaia/TLE fixtures from `data/`, which `scene.py` resolves
    as `_REPO/data` in the dev tree. A non-editable wheel install lands in site-packages where that
    `__file__`-relative path is absent, so the installed CLI resolves the fixtures via the
    TRACKLET_DATA env override — EXACTLY the path the M2 DoD names ("clone -> install -> reproduce"):
    a fresh clone always carries `data/`, and the S3 clean-room sets TRACKLET_DATA to the clone's
    `data/`. Here we install the bare wheel into a throwaway venv (the `installed_venv` fixture,
    deps included), point TRACKLET_DATA at the repo's committed `data/`, and prove the
    wheel-installed CLI reproduces the synthetic residual — the honest full AC-1.2 claim, not a
    dev-venv stand-in."""
    tracklet_cmd = _bin(installed_venv, "tracklet")
    out_dir = tmp_path / "out"
    env = {**os.environ, "TRACKLET_DATA": str(_REPO / "data")}
    out = _run(
        [
            str(tracklet_cmd),
            "--config",
            str(_REPO / "config" / "default_scene.toml"),
            "--out",
            str(out_dir),
        ],
        env=env,
    )
    assert "residual:" in out, f"wheel-installed CLI did not print a residual:\n{out}"
    assert (out_dir / "residual.txt").exists(), "wheel-installed CLI did not write residual.txt"


def _parse_lock_versions(lock_path: Path) -> dict:
    """name(lower, dash-normalized) -> version from a `pip freeze` lockfile (skips comments / VCS /
    editable lines)."""
    out: dict[str, str] = {}
    for raw in lock_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        if "==" not in line:
            continue
        name, _, ver = line.partition("==")
        out[name.strip().lower().replace("_", "-")] = ver.strip()
    return out


def _parse_lower_bound(spec: str):
    """('numpy>=2.4') -> ('numpy', '2.4'). Returns (name, None) if there is no >= bound."""
    import re

    m = re.match(r"^([A-Za-z0-9_.\-]+)", spec)
    name = m.group(1) if m else spec
    gm = re.search(r">=\s*([0-9][0-9A-Za-z.\-]*)", spec)
    return name, (gm.group(1) if gm else None)


def _ver_tuple(ver: str):
    """Numeric-leading version tuple for a <= comparison; non-numeric trailing parts truncate."""
    parts = []
    for chunk in ver.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        if num == "":
            break
        parts.append(int(num))
    return tuple(parts)
