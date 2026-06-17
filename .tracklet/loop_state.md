---
current_milestone: M0
current_increment: "S1 scene + frozen real-data fixtures"
last_increment_id: "S0 environment + plate-solver gate"
phase: BUILD
status: FIX_AWAITING_BUILD
last_green_sha: f87fc9bc6cab4efedbb47bc2285f8173f9ae4944
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 5, failed: 0}
  - {cmd: 'scripts/_smoke_solve.py (S0 @solver gate — formal golden e2e is S7)', passed: 1, failed: 0, residual_arcsec: 14.2}
plan_file: ~/.claude/plans/lucky-dazzling-parasol.md
plan_sha256: d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07
no_progress_count: 1
open_findings:
  - id: F1
    sev: major
    note: >-
      ISS at altitude -84.7 deg (far side of Earth) at the configured obs UTC 2026-06-01T14:00Z —
      camera points at an un-observable target. FIX: resolve obs_utc to a real visible pass
      (ISS altitude > ~20 deg over Perth) near the TLE epoch, and add a FAIL-CLOSED altitude
      assertion in fetch_fixtures.resolve_pointing so a below-horizon scene can never be frozen.
    phase: REVIEW
  - id: F2
    sev: major
    note: >-
      TLE epoch 2026-06-16 was propagated 15.3 days BACK to the obs time -> SGP4 LEO accuracy is
      fiction. FIX: set obs_utc within ~1 day of the TLE epoch (folds into F1 — pick a visible pass
      near the epoch).
    phase: REVIEW
  - id: F3
    sev: major
    note: >-
      Gaia cone radius CONE_RADIUS_DEG=1.6 < field half-diagonal 2.011 deg -> the 2048^2 frame
      corners are STARLESS and the radius comment is wrong. FIX: radius >= ~2.1 deg (half-diagonal +
      margin), fix the comment, re-fetch the cone.
    phase: REVIEW
  - id: F4
    sev: minor
    note: >-
      "idempotent" overstated: re-fetch at a drifted center/date ORPHANS the old fixture, and
      default_catalogue_path/default_tle_path select sorted()[-1] (lexicographic) which can mismatch
      the config center. FIX: fetch_fixtures cleans old fixtures (keep one set) and/or default_*_path
      selects the fixture matching the config center.
    phase: REVIEW
  - id: F5
    sev: minor
    note: >-
      negative-coordinate filename mangle .replace('-','m') runs over the whole string; works only
      because RA>=0. Tighten (mangle the dec part only) OR reject (moot once F4 enforces a single
      committed fixture set).
    phase: REVIEW
  - id: F6
    sev: nit
    note: >-
      REJECTED with rationale: the ascii.read comment-marker would only drop a data row beginning
      with '#', which a numeric Gaia CSV can never produce; reviewer deemed it acceptable. No action.
    phase: REVIEW
next_action: >-
  FIX S1 — re-enter BUILD on the EXISTING branch feat/S1 (do NOT cut a new branch; it already holds the
  S1 build at HEAD). Disposition every open_findings entry: F1+F2 (resolve obs_utc to a REAL visible ISS
  pass — altitude > ~20 deg over Perth — near the TLE epoch, + add a fail-closed altitude assertion in
  fetch_fixtures.resolve_pointing), F3 (Gaia cone radius >= ~2.1 deg + fix the comment), F4 (single
  committed fixture set and/or config-matched default_*_path), F5 (tighten or reject), F6 (already
  rejected). Real fixes via TDD (failing test first). Re-run fetch ONCE to regenerate the frozen fixtures
  + config (new obs_utc + center + wider cone) and re-commit. Then RE-REVIEW (fresh-context local agent
  over `git diff main..feat/S1`): every finding fixed-and-green or rejected-with-rationale AND full
  non-solver suite green -> merge feat/S1 -> main (--no-ff) + INTEGRATE. Use ~/tracklet/.venv/bin/python.
  If the re-review bounces AGAIN, no_progress hits 2 -> human gate at next tick start (§3.3).
human_gate: false
tick_lock: {pid: 92116, started: 2026-06-17T13:00:16+0800}

# --- post-S1-REVIEW-bounce note (read before the FIX tick) ---
# S1 was BUILT on feat/S1 (30/30 non-solver green) but the adversarial review returned REVISE: the
# scene is physically incoherent (ISS below horizon at the obs time, 15-day TLE back-propagation,
# starless field corners). NOT merged. The CURRENT BRANCH IS feat/S1 (HEAD = the S1 build + this bounce
# state commit); main is still at d14a620 / last_green_sha f87fc9b (S0). The FIX tick: GENBA on feat/S1
# (NOT main), status FIX_AWAITING_BUILD -> re-enter BUILD on feat/S1 (do NOT re-branch), fix the
# open_findings via TDD, re-fetch, re-review, then merge feat/S1 -> main. §3.5 for the FIX tick: tree is
# clean on feat/S1; the build + bounce commits are loop/Generator-authored — expected, not an anomaly.
# anti-spin: this review-bounce was a non-green/non-plan-lock tick -> no_progress_count 0->1; the FIX
# tick MUST land green (merge) or no_progress hits 2 and pauses for human.
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

- [tick 3 | GENBA] Thought: scheduled wakeup; state=FRESH, next rung S1; verify §3.5 + plan unchanged + S1's external archives before planning. → Action(Read state; git status/log/HEAD; re-hash plan; curl CelesTrak gp.php + Gaia TAP) → Observation: clean tree @ f8ac53e (expected post-S0 bookkeeping commit), plan SHA matches d7237cdd…, no_progress 0, tick_lock null; CelesTrak 200 + Gaia TAP 200. Perth 11:46.
- [tick 3 | RESEARCH] Thought: S1 (scene + frozen fixtures) carries no genuine technical unknown — the plan (Sprint 1) settles the SceneConfig shape, the Gaia ADQL (ROW_LIMIT=-1, mag<14), and the fetch-validation Poka-Yokes; only external FACTS to confirm are CelesTrak + Gaia reachability → ABBREVIATE, not /deep-research. → Action(1-call reachability confirm, above) → Observation: both archives HTTP 200; no new external dependency introduced. Carried kaizen: Gaia needs certifi-CA + retry (from tick-2 _smoke_solve.py). research: ABBREVIATED (reachability confirmed, JIT).
- [tick 3 | IDEATE] Thought: S1 is fully specified in the plan (Sprint 1, ACs 1.1-1.3) with an obvious module shape (scene.py + fetch_fixtures.py); heavy ideation would be Muda. SKIP. → Action(emit trivial design brief, below) → Observation: brief recorded; Pre-Mortem guard clear — scene DEFINES the scene (reads no truth), fetch writes fixtures (not truth.json); render/solve/detect/measure/score contracts untouched (S1 implements neither); no speculative scope.
- [tick 3 | PLAN] Thought: JIT shortcut — S1 fully covered by the approved plan; skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; update next_action to the S1 BUILD contract) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S1 BUILD is the next tick. no_progress_count stays 0 (plan-lock = progress, §3.3).

### increment design brief (tick 3)

```
S1 — scene + frozen real-data fixtures. Build EXACTLY Sprint 1 of the approved plan
(lucky-dazzling-parasol.md, "Sprint 1", ACs 1.1-1.3). The S1 BUILD tick runs /tdd-harness with the
plan as contract (S0 created the test runner, so the harness can now preflight).

SCOPE (JIT — Sprint 1 verbatim):
  - src/tracklet/scene.py: `SceneConfig` frozen dataclass + `build_scene(config_path) -> SceneConfig`
    loading config/default_scene.toml. Validation Poka-Yoke (fail-closed): assert W*pixel_scale ≈ FOV
    (consistency), positive dims, sane mag limit. Pure; reads NO truth (it DEFINES the scene).
  - scripts/fetch_fixtures.py: run-once-then-offline. CelesTrak gp.php?CATNR=25544&FORMAT=tle ->
    data/tle/iss_<date>.txt; Gaia DR3 launch_job_async ADQL cone (EXPLICIT table gaiadr3.gaia_source,
    SELECT ra,dec,phot_g_mean_mag, CONTAINS(...CIRCLE(ra0,dec0,radius)), phot_g_mean_mag<14, with
    Gaia.ROW_LIMIT=-1 so the star field is NOT silently truncated) -> data/catalogue/gaia_<center>.csv.
    Idempotent; stamps source URL + query + UTC fetch time. REUSE certifi-CA + retry-with-backoff from
    scripts/_smoke_solve.py.
  - Fetch-validation Poka-Yoke (fixtures are the foundation of every downstream test — reject garbage
    BEFORE committing): TLE parses as two 69-char lines with valid checksums (reject HTML error pages
    CelesTrak returns on bad CATNR/rate-limit); Gaia CSV non-empty, expected columns, plausible star
    count (> a few hundred for a 2.8deg field at mag<14). Bad TLE / truncated|empty Gaia -> hard error,
    NO snapshot written.
  - Run fetch ONCE and COMMIT the frozen TLE + Gaia CSV under data/ (small, public/open: Gaia DR3 +
    CelesTrak). The run/test path is then fully OFFLINE against committed fixtures.

TOUCHED MODULES: src/tracklet/scene.py (implement stub) + scripts/fetch_fixtures.py (implement stub) +
data/ (new frozen fixtures) + tests/test_scene.py (+ a fetch-validation test fed malformed TLE/empty
CSV). render/solve_pointing/detect_streak/measure_position/score/report/run stubs UNTOUCHED.

DATA FLOW: config/default_scene.toml -> build_scene -> SceneConfig (consumed later by render in S2).
fetch_fixtures (online, once) -> data/{tle,catalogue} (frozen, committed) -> loaded offline downstream.

SEALED-TRUTH: preserved by construction. scene defines scene params (no truth read). fetch_fixtures
writes catalogue/TLE fixtures, NOT truth.json (truth is written only by render in S2, read only by
score in S5). No solving module touched.

TEST ORACLE (AC 1.1-1.3, all offline against committed fixtures / fed fakes):
  1.1 SceneConfig deterministic + validation REJECTS inconsistent FOV/pixel-scale/dims (test feeds a bad
      config, expects a raise).
  1.2 frozen TLE + Gaia CSV load OFFLINE (test loads committed fixtures, no network).
  1.3 fetch_fixtures idempotent + provenance-stamped + validates output (test feeds malformed TLE /
      empty CSV -> hard error, no snapshot). `pytest -m "not solver"` stays green.

YAGNI / OUT OF SCOPE: NO rendering, NO WCS, NO PSF/noise (all S2); NO solving/detection/scoring; NO
network in the run/test path (only fetch_fixtures touches the network, and only when run explicitly).

JUDGE SCORE TABLE: N/A — heavy ideation SKIPPED (S1 fully specified, no fork). Pre-Mortem guard manual,
all four clear: (a) re-invents nothing (scene/fetch are empty stubs); (b) sealed-truth untouched;
(c) shatters no signed contract; (d) scope == Sprint 1 verbatim.
```

- [tick 4 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S1; verify PHASE-4 gates + baseline green before building. → Action(Read state; git status/log/HEAD; re-hash plan; baseline pytest) → Observation: clean tree @ d14a620, plan SHA matches d7237cdd…, no_progress 0, only loop-authored commits since f87fc9b, baseline 5/5 green. Cut feat/S1.
- [tick 4 | BUILD] Thought: S0 created the test runner → build S1 under TDD via a spawned Generator (parent stays lean). → Action(spawn general-purpose Generator on feat/S1: implement scene.py + fetch_fixtures.py, resolve pointing via skyfield, fetch+commit frozen fixtures, TDD ACs 1.1-1.3) → Observation: Generator DONE — 6 commits (RED→GREEN×2 + freeze + refactor) 30aa0ab..39cb52d; scene.py + fetch_fixtures.py + config(center resolved RA35.528/Dec26.548) + tests/test_scene.py + tests/test_fetch_fixtures.py + data/{tle,catalogue} fixtures (1500-star Gaia cone). INDEPENDENTLY VERIFIED by parent: 30/30 non-solver green, tree clean, scope held (no foreign module edits), sealed-truth grep clean (only docstrings).
- [tick 4 | REVIEW] Thought: real product behavior + a pointing sub-decision adjacent to sealed-truth → fresh-context adversarial review (free, local). → Action(spawn general-purpose reviewer over `git diff main..feat/S1`) → Observation: VERDICT REVISE. Sealed-truth NON-CIRCULARITY SURVIVES (clean — config center is public pointing, not truth; measure reads only the solved WCS); tests honest (identity probe: neutering _validate fails 7 tests). But 3 MAJOR physical-validity defects → F1 (ISS alt −84.7° = far side of Earth at obs time), F2 (TLE propagated 15.3 d back from epoch → SGP4 fiction), F3 (Gaia cone 1.6° < field half-diagonal 2.011° → starless corners); + F4/F5 MINOR; F6 NIT rejected. GATE = REVISE → NOT mergeable; bounce to FIX_AWAITING_BUILD per §3.2.
- [tick 4 | HANSEI] What worked: the spawned-Generator build kept the parent lean (~110K tok of build returned one compact report); and the FRESH-CONTEXT REVIEW EARNED ITS KEEP — it caught a physical-validity defect (satellite below the horizon) that ALL 30 tests passed straight through, because the tests never asserted observability. Textbook proof that green-under-its-own-tests is necessary, not sufficient. Root cause (muda): the obs UTC was an S0 config placeholder never sanity-checked against the ISS geometry; the Generator faithfully built to a physically-incoherent config. KAIZEN (FIX tick): resolve obs_utc to a REAL visible pass (ISS altitude >~20° over Perth) near the TLE epoch, and make satellite-above-horizon + TLE-epoch-proximity a FAIL-CLOSED VALIDATION POKA-YOKE in resolve_pointing, so a nonsensical scene can never be frozen again. Anti-spin (§3.3): this build tick bounced (no merge, no plan-lock) → no_progress_count 0→1; the FIX tick MUST merge green to reset (a second consecutive non-green tick trips the human gate).
