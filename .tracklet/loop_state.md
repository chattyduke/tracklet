---
current_milestone: M0
current_increment: "S1 scene + frozen real-data fixtures"
last_increment_id: "S0 environment + plate-solver gate"
phase: HANSEI
status: FRESH
last_green_sha: f87fc9bc6cab4efedbb47bc2285f8173f9ae4944
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 5, failed: 0}
  - {cmd: 'scripts/_smoke_solve.py (S0 @solver gate — formal golden e2e is S7)', passed: 1, failed: 0, residual_arcsec: 14.2}
plan_file: ~/.claude/plans/lucky-dazzling-parasol.md
plan_sha256: d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07
no_progress_count: 0
open_findings: []
next_action: >-
  S1 (Sprint 1: scene + frozen real-data fixtures) is the next rung. Next tick opens FRESH ->
  GENBA -> RESEARCH (ABBREVIATE: confirm CelesTrak gp.php + Gaia TAP reachable; Gaia needs the
  certifi CA fix — reuse the pattern in scripts/_smoke_solve.py) -> IDEATE (SKIP, S1 fully specified
  in the plan) -> PLAN (JIT shortcut: consume the approved plan, same SHA) -> end
  PLAN_LOCKED_AWAITING_BUILD.
human_gate: false
tick_lock: null

# --- post-S0 note (read before the next BUILD tick's §3.5 gate) ---
# S0 merged GREEN at last_green_sha f87fc9b (`git log` shows the --no-ff merge). main HEAD after
# this tick is the bookkeeping commit ONE PAST f87fc9b — this is the expected post-integration
# state, NOT a §3.5 anomaly (a FRESH planning tick does not build, so no HEAD==last_green_sha gate
# fires this tick). The S1 BUILD tick will branch feat/S1 off main's then-HEAD and record its own
# expected post-plan commit. Out-of-repo S0 footprint (per README): brew astrometry-net, ~335MB in
# ~/tracklet/indexes (gitignored), and one add_path line in /opt/homebrew/etc/astrometry.cfg.
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

- [tick 2 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S0; verify §3.5 gates + env feasibility before a long system-mutating build. → Action(Read state; git status/log/HEAD; re-hash plan; probe brew/python/solve-field/network) → Observation: clean tree @ bootstrap 0033462, plan SHA matches, no_progress 0, tick_lock null; env feasible (brew + py3.14.4 + py3.12 present; data.astrometry.net / PyPI / CelesTrak all HTTP 200). Cut feat/S0.
- [tick 2 | BUILD] Thought: /tdd-harness PREFLIGHT cannot run for S0 — it requires a working test runner, which S0 itself creates (chicken-egg / Andon). Build S0 under the inner test-driven-development discipline + konnyaku directly; /tdd-harness resumes from S1. → Action(scaffold 24 files; venv on py3.14 — ALL cp314 wheels resolved, no 3.12 fallback needed; TDD the version guard RED→GREEN; pin requirements.lock; brew install astrometry-net; install_indexes.sh fetched 4107–4113 ~335MB + wired astrometry.cfg; _smoke_solve.py real-Gaia xylist blind solve) → Observation: AC 0.1–0.6 all green; 5/5 non-solver tests; smoke blind-solve PASS @14.2"; decisively re-confirmed solving ONLY our indexes (Cellar data dir empty). Commits 87b219a..135281d.
- [tick 2 | REVIEW] Thought: large diff (>8 files) → fresh-context adversarial LOCAL review (no cloud, §6). → Action(spawn general-purpose reviewer over `git diff main..feat/S0`) → Observation: VERDICT ACCEPT_WITH_NOTES; sealed-truth provably preserved, guard non-tautologically tested (reviewer neutered the guard → test failed), install_indexes.sh fail-closed verified. Dispositioned — FIXED: pythonpath=[src] (verified bare pytest 5/5 with tracklet uninstalled), requires-python >=3.14,<3.15, smoke offset-gate <60", smoke TemporaryDirectory cleanup + Gaia retry-resilience; REJECTED w/ rationale: committed tick_lock (loop's required memory; cleared this tick) + cfg-write NIT (set -e already fails loud). Re-smoke PASS @14.2". Fix commit 46c6d33.
- [tick 2 | INTEGRATE] Thought: PHASE-5 gate met (every finding dispositioned + non-solver suite green + smoke green) → integrate. → Action(git merge --no-ff feat/S0 → main; pytest; delete feat/S0) → Observation: merged @ f87fc9b (S0 green here); 5/5 green on main; branch deleted. S0 ≠ a milestone (M0 needs S0–S7) → no tag.
- [tick 2 | HANSEI] What worked: backgrounding the long poles (venv install + 340MB index fetch) while scaffolding in parallel kept the tick flowing; genchi-genbutsu probes (Cellar-empty check, `--config`-only re-solve, the SSL diagnosis) each caught a real trap before it bit (spurious-pass risk; env-SSL). py3.14 carried every cp314 wheel → no 3.12 fallback. Surprises/Muda: (1) /tdd-harness cannot preflight the increment that creates its own test runner — S0 is inherently pre-harness; (2) python.org stdlib ssl ships no CA bundle → Gaia TLS failed until pointed at certifi; (3) the Gaia archive is flaky (one ConnectionReset) → added retry. KAIZEN for next tick: S1's fetch_fixtures hits the SAME Gaia SSL + flakiness — reuse the certifi-CA + retry pattern from scripts/_smoke_solve.py from the start rather than rediscovering it. Loop-doc kaizen: S0 builds via direct TDD (not /tdd-harness); the harness applies from S1 onward once a test runner exists.
