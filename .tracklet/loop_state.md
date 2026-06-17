---
current_milestone: M0
current_increment: "S0 environment + plate-solver gate"
last_increment_id: null
phase: PLAN
status: PLAN_LOCKED_AWAITING_BUILD
last_green_sha: null
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 0, failed: 0}
  - {cmd: 'make test-golden', passed: 0, failed: 0, residual_arcsec: null}
plan_file: ~/.claude/plans/lucky-dazzling-parasol.md
plan_sha256: d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07
no_progress_count: 0
open_findings: []
next_action: >-
  BUILD S0 (Sprint 0 of the approved plan) via /tdd-harness. Cut feat/S0 off main.
  Scope = scaffold + venv-gate + plate-solver gate (see design brief below). Index-fetch
  failure is a HARD HALT per Andon §4.2 #4 — do NOT proceed to S1. S0's executable gate is
  the smoke solve (AC-0.5) yielding an astropy-loadable WCS.
human_gate: false
tick_lock: null

# --- bootstrap note (this FRESH tick created the repo + this state file) ---
# last_green_sha is null because no milestone is green yet (M0 not reached).
# The §3.5 clean-tree/SHA gate for the NEXT (BUILD) tick is satisfied by ALL of:
#   (1) `git status --porcelain` empty (clean tree), AND
#   (2) status == PLAN_LOCKED_AWAITING_BUILD, AND
#   (3) main has exactly ONE commit (the bootstrap commit) and HEAD points at it
#       — verify with `git -C ~/tracklet log --oneline` (single line) before building.
# If any foreign commit/dirty file appears, Andon-halt (§4) instead of building.
---

## decisions log (append-only ReAct triples; newest last)

- [tick 1 | GENBA] Thought: first tick, no state file, `~/tracklet` absent → FRESH bootstrap tick per §3.2. → Action(Bash: stat ~/tracklet + git status + plan-exists check; Read lucky-dazzling-parasol.md in full) → Observation: `~/tracklet` did not exist; approved plan present (27528 bytes, SHA d7237cdd…f73f07); Perth time 23:33 (past the nightly soft-cutoff). Classified FRESH.
- [tick 1 | RESEARCH] Thought: S0 = environment + plate-solver gate; fully specified as Sprint 0 in the approved plan; index strategy (4100-series + 4200 drop-in + ASTAP fallback) and loud-fail Poka-Yoke already settled; live fetch-verification belongs in the BUILD tick (`install_indexes.sh` fails loud per §4.2 #4). → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical; S0 settled by the approved plan).
- [tick 1 | IDEATE] Thought: S0 has no design fork — it is environment setup with 6 signed ACs (0.1–0.6) in the plan; heavy ideation would be Muda. SKIP. → Action(emit trivial design brief, below) → Observation: brief recorded; sealed-truth Poka-Yoke + all 7 module contracts untouched by construction (S0 builds no product module).
- [tick 1 | PLAN] Thought: JIT shortcut — S0 fully covered by the approved `~/.claude/plans/lucky-dazzling-parasol.md`; skip `/ultraplan`, consume it directly, record path + SHA256 so the BUILD tick's SHA gate still applies. → Action(shasum -a 256 plan; `git init -b main ~/tracklet`; write .gitignore + this state file; commit as bootstrap) → Observation: plan_sha256 = d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07; bootstrap committed to main (SHA: see `git log`); status set PLAN_LOCKED_AWAITING_BUILD. Per §3.2 the FRESH tick HARD-STOPS here at the plan lock; the S0 build is the NEXT tick.

### increment design brief (tick 1)

```
S0 — Environment & plate-solver gate. Build EXACTLY Sprint 0 of the approved plan
(lucky-dazzling-parasol.md, "Sprint 0", lines ~145–179), no more, no less.

SCOPE (JIT — Sprint 0 verbatim):
  - Scaffold ~/tracklet: pyproject.toml, requirements.lock, Makefile (setup|fetch|run|test|test-golden),
    README.md, LICENSE, config/default_scene.toml, scripts/{fetch_fixtures.py, install_indexes.sh},
    data/, src/tracklet/{__init__,scene,render,solve_pointing,detect_streak,measure_position,score,report,run}.py
    (stub modules only — implementation is S1–S7), tests/ skeleton. (.gitignore already created this tick.)
  - Python gate (Poka-Yoke, fail-closed): create .venv on Python 3.14; pip install astropy, astroquery,
    skyfield, opencv-python, scikit-image, matplotlib, numpy, scipy, photutils, pytest. On the FIRST wheel
    failure, tear down the WHOLE venv and rebuild on `brew install python@3.12` — never pip-patch one lib.
    Pin the exact interpreter patch + all versions into requirements.lock; add a runtime MINOR-version
    assertion (3.12.x — minor only, not exact patch) in conftest.py + run.py that fails loud on a wrong minor.
  - `brew install astrometry-net`; verify `solve-field --help`. Run scripts/install_indexes.sh to fetch the
    ~340MB 4100-series wide-field indexes (4107..4113); drop into an index dir; append add_path + autoindex to
    astrometry.cfg. 4200-series is a drop-in equivalent; 5200 would also work — standardize on 4100/4200 for
    ONE reproducible recipe.
  - INDEX-FETCH FAILURE IS A HARD HALT (Andon §4.2 #4): if data.astrometry.net 404s/rate-limits and the ASTAP
    download is also unreachable, install_indexes.sh fails loud and S0 STOPS — do NOT proceed to S1. A
    non-runnable make test-golden is NOT a green M0.
  - Smoke solve a known star field (or an astrometry.net sample) → a .wcs that astropy.wcs.WCS can read. This
    is what CONFIRMS the fetched index subset actually works.
  - ASTAP fallback made executable: scripts/install_indexes.sh --astap downloads astap + d50 DB, codesigns,
    verifies astap solves the same smoke field — OR explicitly document it as the recovery path.

TOUCHED MODULES: NONE of the 7 product modules are implemented in S0 (stubs only). The sealed-truth Poka-Yoke
and every signed module contract (render / solve_pointing / detect_streak / measure_position / score) are
therefore untouched and preserved by construction.

DATA FLOW: n/a (no pipeline code in S0).

TEST ORACLE (S0's executable gate): AC-0.2 = .venv imports all libs AND the minor-version assertion trips on a
wrong-minor interpreter; AC-0.3 = `solve-field --help` runs; AC-0.5 = smoke solve yields an astropy-loadable
WCS (THE gate); AC-0.6 = ASTAP fallback verified OR documented. Plan execution-note: "Sprint 0 is the gate: do
not start Sprint 1 until the smoke solve passes and the venv imports clean." `pytest -m "not solver"` must be
green (trivially — no product behavior yet); the @solver smoke solve is the real S0 proof.

YAGNI / OUT OF SCOPE: no product-module implementation (that is S1–S7), no fixtures fetch (S1), no
solver-abstraction/strategy layer (one solver; ASTAP = documented manual fallback), no network in the run/test
path.

JUDGE SCORE TABLE: N/A — heavy ideation SKIPPED (S0 is a fully-specified, no-fork environment increment; a
brainstorm→judge panel here would be Muda). Pre-Mortem guard checked manually, all four clear:
  (a) re-invents nothing — repo is empty;
  (b) sealed-truth untouched — no module built;
  (c) shatters no signed contract — no module built;
  (d) no speculative scope — scope == Sprint 0 verbatim.
```
