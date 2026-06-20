"""S4 tests — `.github/workflows/ci.yml` is authored + STATICALLY valid (AC 4.1–4.4).

The CI is validated **statically only** — these tests parse the YAML and assert structure; they do
NOT run GitHub Actions (no remote; the cross-arch x86_64-Linux greenness is the S6 human-gated
Actions run, never faked here). The point is a Poka-Yoke: a CI regression (a dropped version floor, a
relaxed Python pin, a snuck-in push/secret step) is caught LOCALLY before the human push, not after.

The workflow MIRRORS the locally-proven recipes:
  - `pip install . -c requirements.lock` (S1 lockfile install) + the `dev` extra,
  - `./scripts/install_indexes.sh` (S3 cross-platform index wiring),
  - `pytest -m "not solver"` / `pytest -m solver` (the existing markers),
  - the `score` 10" residual gate (the golden e2e's own assertion is the gate).
No new threshold, no new install logic, no deploy/secrets/push.

These tests must genuinely BITE: deleting the version-floor assertion, relaxing the 3.14 pin, or
adding a `secrets.`/push-action step must turn one of them red.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_REPO = Path(__file__).resolve().parent.parent
_CI = _REPO / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    """Parse ci.yml once (AC 4.1: it exists + is valid YAML)."""
    assert _CI.exists(), f"CI workflow missing: {_CI}"
    data = yaml.safe_load(_CI.read_text())
    assert isinstance(data, dict), "ci.yml must parse to a mapping"
    return data


@pytest.fixture(scope="module")
def raw() -> str:
    """The raw workflow text (for substring/regex assertions over step bodies)."""
    return _CI.read_text()


def _job(workflow: dict, name: str) -> dict:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "ci.yml must declare a `jobs:` mapping"
    assert name in jobs, f"missing job `{name}`; have {sorted(jobs)}"
    return jobs[name]


def _steps_text(job: dict) -> str:
    """Concatenate every `run:`/`uses:`/`with:` body of a job into one searchable blob."""
    parts: list[str] = []
    for step in job.get("steps", []):
        if not isinstance(step, dict):
            continue
        for key in ("run", "uses", "name"):
            val = step.get(key)
            if isinstance(val, str):
                parts.append(val)
        with_block = step.get("with")
        if isinstance(with_block, dict):
            for v in with_block.values():
                parts.append(str(v))
    return "\n".join(parts)


# --------------------------------------------------------------------------- AC 4.1


def test_ci_is_valid_yaml_and_has_both_jobs(workflow: dict) -> None:
    """AC 4.1: valid YAML; declares `unit` + `golden-solver` jobs."""
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    assert "unit" in jobs, "missing the fast `unit` job"
    assert "golden-solver" in jobs, "missing the `golden-solver` job"


def test_both_jobs_run_on_ubuntu_latest(workflow: dict) -> None:
    """AC 4.1: both jobs run on ubuntu-latest (the x86_64-Linux clean machine)."""
    for name in ("unit", "golden-solver"):
        job = _job(workflow, name)
        assert job.get("runs-on") == "ubuntu-latest", (
            f"job `{name}` must run-on ubuntu-latest, got {job.get('runs-on')!r}"
        )


def test_both_jobs_pin_python_314(workflow: dict) -> None:
    """AC 4.1: both jobs set up Python 3.14 via actions/setup-python (honors the _env guard).

    Bites if the 3.14 pin is relaxed to another minor.
    """
    for name in ("unit", "golden-solver"):
        job = _job(workflow, name)
        setup_steps = [
            s
            for s in job.get("steps", [])
            if isinstance(s, dict) and "setup-python" in str(s.get("uses", ""))
        ]
        assert setup_steps, f"job `{name}` must use actions/setup-python"
        versions = {str(s.get("with", {}).get("python-version", "")) for s in setup_steps}
        assert any(v.startswith("3.14") for v in versions), (
            f"job `{name}` must pin Python 3.14 (the _env guard), got {versions!r}"
        )
        # Must NOT relax to a different minor as the configured runtime.
        assert not any(
            v and not v.startswith("3.14") for v in versions
        ), f"job `{name}` setup-python pins a non-3.14 minor {versions!r} — the _env guard is 3.14"


# --------------------------------------------------------------------------- AC 4.2


def test_unit_installs_from_lockfile_and_runs_non_solver(workflow: dict) -> None:
    """AC 4.2: `unit` installs `pip install . -c requirements.lock` (+dev) + `pytest -m "not solver"`."""
    job = _job(workflow, "unit")
    body = _steps_text(job)
    assert "requirements.lock" in body, "`unit` must install with the lockfile constraints"
    assert re.search(r"pip install\b.*\.\b.*-c\s+requirements\.lock", body) or (
        "pip install" in body and "-c requirements.lock" in body
    ), "`unit` must `pip install . -c requirements.lock`"
    assert "[dev]" in body or "'.[dev]'" in body or '".[dev]"' in body, (
        "`unit` must install the `dev` extra (pytest)"
    )
    assert 'pytest -m "not solver"' in body or "pytest -m 'not solver'" in body, (
        "`unit` must run `pytest -m \"not solver\"`"
    )


# --------------------------------------------------------------------------- AC 4.3


def test_golden_installs_solver_with_version_floor(workflow: dict, raw: str) -> None:
    """AC 4.3: `golden-solver` apt-installs astrometry.net AND asserts a >= 0.80 version floor.

    Bites if the version-floor assertion line is deleted.
    """
    job = _job(workflow, "golden-solver")
    body = _steps_text(job)
    assert "astrometry.net" in body, "`golden-solver` must apt-get install astrometry.net (solve-field)"
    assert "solve-field --version" in body, (
        "`golden-solver` must check `solve-field --version` for the version floor"
    )
    # The concrete >= 0.80 floor must be present (the named version-floor assertion).
    assert "0.80" in body, "`golden-solver` must assert the concrete solve-field >= 0.80 version floor"


def test_golden_documents_ppa_build_fallback(raw: str) -> None:
    """AC 4.3: a too-old solver has a documented build/PPA fallback (a comment is enough)."""
    low = raw.lower()
    assert ("ppa" in low) or ("build from source" in low) or ("build/ppa" in low), (
        "the version-floor must document a build/PPA fallback for a too-old solver"
    )


def test_golden_wires_indexes_via_install_script(workflow: dict) -> None:
    """AC 4.3: `golden-solver` wires the indexes via the cross-platform install_indexes.sh (S3)."""
    job = _job(workflow, "golden-solver")
    body = _steps_text(job)
    assert "install_indexes.sh" in body, (
        "`golden-solver` must wire indexes via scripts/install_indexes.sh (S3 cross-platform)"
    )


def test_golden_caches_indexes(workflow: dict) -> None:
    """AC 4.3: the ~340 MB indexes are cached (actions/cache) — a cache MISS still downloads + the
    install_indexes Andon hard-stop fails the job loudly on a 404/rate-limit (honest red, not a hang)."""
    job = _job(workflow, "golden-solver")
    body = _steps_text(job)
    assert "actions/cache" in body, "`golden-solver` must cache the indexes (actions/cache)"


def test_golden_runs_solver_marker_and_gates_on_residual(workflow: dict) -> None:
    """AC 4.3: `golden-solver` runs `pytest -m solver` — the golden e2e's own 10" residual assertion
    is the gate (a residual >= 10" fails the test → fails the job). No NEW threshold."""
    job = _job(workflow, "golden-solver")
    body = _steps_text(job)
    assert "pytest -m solver" in body or "pytest -m 'solver'" in body or 'pytest -m "solver"' in body, (
        "`golden-solver` must run `pytest -m solver` (the golden e2e is the residual gate)"
    )


def test_golden_sets_tracklet_data_for_fixtures(workflow: dict, raw: str) -> None:
    """AC 4.3 (S1/S3 finding): the golden-solver job must set TRACKLET_DATA so the checked-out
    synthetic run finds the committed `data/` fixtures (carries the run.py/scene.py env override)."""
    job = _job(workflow, "golden-solver")
    body = _steps_text(job)
    # TRACKLET_DATA may appear in a step `env:` block (not captured by _steps_text), so also scan raw.
    assert "TRACKLET_DATA" in body or "TRACKLET_DATA" in raw, (
        "the golden-solver job must set TRACKLET_DATA so the run finds the committed data/ fixtures"
    )


# --------------------------------------------------------------------------- AC 4.4 (honesty / no-push)


def test_no_push_deploy_secret_or_publish_action(raw: str, workflow: dict) -> None:
    """AC 4.4: there is NO push/deploy/secret/publish ACTION anywhere in the workflow.

    The `on: [push, pull_request]` TRIGGER is fine (it is how CI fires) — but there must be no
    `git push`, no deploy/publish action, and no `secrets.` reference. Bites if any is snuck in.
    """
    low = raw.lower()
    # No secrets ever (the workflow needs none; a `secrets.` reference would be a red flag).
    assert "secrets." not in low, "the workflow must reference NO secrets"
    # No git-push action in any step body.
    assert "git push" not in low, "the workflow must contain no `git push` step"
    # No publish/deploy actions.
    for banned in ("pypa/gh-action-pypi-publish", "twine upload", "actions/deploy-pages", "softprops/action-gh-release"):
        assert banned not in low, f"the workflow must contain no publish/deploy action ({banned})"
    # Defensive: scan every job's step bodies for a deploy/publish verb in a `run:`/`uses:`.
    for job_name, job in workflow.get("jobs", {}).items():
        body = _steps_text(job).lower()
        assert "git push" not in body, f"job `{job_name}` must not git-push"
        assert "secrets." not in body, f"job `{job_name}` must not use secrets"


def test_on_trigger_is_push_pullrequest_not_a_push_action(workflow: dict) -> None:
    """AC 4.4: the `on:` trigger is push/pull_request (correct) — confirming the `push` token is a
    TRIGGER, not a deploy action. (PyYAML parses the bare `on:` key as the boolean True.)"""
    on = workflow.get("on", workflow.get(True))
    assert on is not None, "ci.yml must declare an `on:` trigger"
    # Normalize the trigger into a set of event names regardless of list/dict YAML form.
    if isinstance(on, str):
        events = {on}
    elif isinstance(on, list):
        events = set(on)
    elif isinstance(on, dict):
        events = set(on.keys())
    else:
        events = set()
    assert "push" in events, "CI should fire on push (the trigger — NOT a deploy step)"
    assert "pull_request" in events, "CI should fire on pull_request"
