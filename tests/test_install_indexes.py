"""S3 tests — install_indexes.sh::find_cfg() is cross-platform (macOS brew + Linux apt).

AC 3.1: ``find_cfg()`` must resolve a valid ``astrometry.cfg`` on BOTH macOS (brew, live on this
machine) AND a stubbed Linux filesystem layout (``/etc/astrometry.cfg`` under an injected writable
temp root) — driven by an INJECTABLE search root (positional args) and/or a ``TRACKLET_ASTROMETRY_CFG``
env override, NOT by hardcoding more ``find`` roots.

These are shell-function tests: we ``source`` the script and call ``find_cfg`` in a subshell, so the
unit under test is the real bash function (no Python re-implementation). They run under
``pytest -m "not solver"`` (no solver / no network)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO / "scripts" / "install_indexes.sh"


def _find_cfg(*args: str, env_override: str | None = None, extra_env: dict | None = None) -> str:
    """Source install_indexes.sh and call its find_cfg with the given positional search roots.

    Returns the trimmed stdout (the resolved cfg path). We invoke find_cfg directly so the test
    exercises the REAL shell function, not a Python port. ``set -e`` in the script is disabled for
    the sourced call (``set +e``) so a non-fatal ``find`` miss inside the function does not abort the
    subshell before ``find_cfg`` can return its default.
    """
    roots = " ".join(f'"{a}"' for a in args)
    env_line = f'export TRACKLET_ASTROMETRY_CFG="{env_override}"; ' if env_override else ""
    snippet = (
        f"set +e; source '{_SCRIPT}'; {env_line}find_cfg {roots}"
    )
    import os

    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        ["bash", "-c", snippet],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, f"find_cfg failed: {proc.stderr}\n{proc.stdout}"
    return proc.stdout.strip()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required to source the script")
def test_find_cfg_resolves_stubbed_linux_layout(tmp_path: Path) -> None:
    """A stubbed apt/Linux layout: <root>/etc/astrometry.cfg under an injected writable temp root.

    The Linux CI runner has its cfg at /etc/astrometry.cfg; we inject <tmp>/etc/astrometry.cfg as the
    same shape under a writable root and require find_cfg to resolve THAT file via an injected search
    root — proving the function is no longer hardcoded to /opt/homebrew /usr/local only.
    """
    etc = tmp_path / "etc"
    etc.mkdir(parents=True)
    cfg = etc / "astrometry.cfg"
    cfg.write_text("# stub linux astrometry.cfg\n")

    resolved = _find_cfg(str(tmp_path))
    assert Path(resolved) == cfg, f"expected the stubbed linux cfg, got {resolved!r}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required to source the script")
def test_find_cfg_env_override_wins(tmp_path: Path) -> None:
    """TRACKLET_ASTROMETRY_CFG is an explicit override that wins over any search-root discovery."""
    override = tmp_path / "custom" / "astrometry.cfg"
    override.parent.mkdir(parents=True)
    override.write_text("# explicit override cfg\n")

    # Even with an unrelated (and cfg-bearing) search root, the explicit override must win.
    other = tmp_path / "other"
    (other / "etc").mkdir(parents=True)
    (other / "etc" / "astrometry.cfg").write_text("# decoy\n")

    resolved = _find_cfg(str(other), env_override=str(override))
    assert Path(resolved) == override, f"env override should win, got {resolved!r}"


@pytest.mark.skipif(
    not Path("/opt/homebrew/etc/astrometry.cfg").exists(),
    reason="macOS brew astrometry.cfg not present (live-path check only on the dev mac)",
)
def test_find_cfg_resolves_macos_brew_live() -> None:
    """The live macOS brew path is UNCHANGED: default roots still resolve the brew cfg."""
    resolved = _find_cfg()  # no injected roots -> falls back to the built-in default roots
    assert Path(resolved).name == "astrometry.cfg"
    assert Path(resolved).exists(), f"resolved cfg does not exist: {resolved!r}"
    # On this dev mac the brew cfg is the canonical one.
    assert "homebrew" in resolved or resolved == "/opt/homebrew/etc/astrometry.cfg"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required to source the script")
def test_find_cfg_falls_back_to_default_when_nothing_found(tmp_path: Path) -> None:
    """With an empty injected root and no env override, find_cfg still emits a non-empty default
    (it never returns an empty string — the caller always gets a path to attempt to wire)."""
    empty = tmp_path / "empty"
    empty.mkdir()
    resolved = _find_cfg(str(empty))
    assert resolved, "find_cfg must always emit a non-empty default cfg path"
    assert resolved.endswith("astrometry.cfg")
