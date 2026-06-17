---
current_milestone: M0
current_increment: "S3 solve_pointing (blind plate-solve)"
last_increment_id: "S2 render (synthetic scene + sealed truth)"
phase: HANSEI
status: FRESH
last_green_sha: 6815c325950c1767486557c29d67e17111f9edd5
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 60, failed: 0}
  - {cmd: 'scripts/_smoke_solve.py (S0 @solver gate — formal golden e2e is S7)', passed: 1, failed: 0, residual_arcsec: 14.2}
plan_file: ~/.claude/plans/lucky-dazzling-parasol.md
plan_sha256: d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07
no_progress_count: 0
open_findings: []  # S2 review (mandatory 2nd pass) ACCEPT @ tick 7; 2 NITs rejected-for-S2; streak-brightness carried as an S3 watch-item (see next_action + tick-7 hansei)
next_action: >-
  S3 (Sprint 3: solve_pointing — blind plate-solve) is the next rung — the FIRST @solver increment and
  HIGH-RISK (WCS / plate-solve path). Next tick opens FRESH -> GENBA -> RESEARCH (SKIP — solver + indexes
  already installed at S0; the de-risk is empirical, done in the BUILD not via /deep-research) -> IDEATE
  (BRIEF design brief: solve_pointing(image_path, scale_hint) -> SolveResult|SolveFailure; headless blind
  solve-field --scale-units degwidth --scale-low/high from the camera model, --downsample 2 --no-plots
  --overwrite, NO --ra/--dec seed; parse .wcs -> astropy WCS; SolveFailure (not exception) on no-solve;
  reads NO truth) -> PLAN (JIT shortcut: Sprint 3 ACs 3.1-3.3, same SHA; lock + end at ExitPlanMode).
  CARRIED S3 WATCH-ITEM (from the S2 review): the rendered streak peak (~162k e) is very bright and the
  _STREAK_PEAK_E=8e3 constant in render.py is misleading vs the actual peak; the plan's Sprint 3 warns a
  bright/saturated streak can spawn spurious solve-field detections — so AC 3.1 (real blind solve on the
  GOLDEN STREAKED frame) must be run for real, and if the streak perturbs the solve, mitigate per the plan
  (cap streak peak brightness in render.py + fix that constant to be honest, OR --downsample, then coarse
  pointing hint, then ASTAP). The S3 BUILD's @solver test (AC 3.1) is run with ~/tracklet/.venv/bin/python
  against the rendered frame; S3's review is HIGH-RISK -> mandatory 2nd local pass.
human_gate: false
tick_lock: null

# --- post-S2 note (read before the next PLAN/BUILD tick) ---
# S2 (render) merged GREEN at last_green_sha 6815c32 (--no-ff); the SEAL is real + adversarially verified
# (image.fits WCS-free via raw-header check; render sole truth.json writer; solving signatures byte-identical
# to main → non-circularity survives; off-center flux-centroid 0.03px → no CD-sign/Y-flip bug; 5/5 mutation
# probes caught). main HEAD after this tick is the bookkeeping commit one past 6815c32 — expected, NOT a §3.5
# anomaly (FRESH planning tick does not build). render artifacts: render_scene(scene, catalogue, tle, out_dir)
# -> RenderResult; image.fits + truth.json under out_dir (gitignored). NEXT rung S3 (solve_pointing, FIRST
# @solver increment, HIGH-RISK). S3 WATCH-ITEM (carried from the S2 review): streak peak ~162k e is bright +
# the _STREAK_PEAK_E constant is misleading — AC 3.1 blind-solves the real streaked frame; if it perturbs the
# solve, cap streak brightness (+ fix the constant) / --downsample / hint / ASTAP per plan Sprint 3.
# venv ~/tracklet/.venv (Python 3.14.4); solve-field + 4100 indexes installed at S0.
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

- [tick 5 | GENBA] Thought: status FIX_AWAITING_BUILD on feat/S1, no_progress 1; verify gates + baseline before fixing. → Action(Read state + 6 findings; git branch/HEAD/clean; plan SHA; baseline pytest) → Observation: on feat/S1 @ a4bbe01, clean, main @ d14a620, only feat/S1 live (branch hygiene OK), plan SHA matches, baseline 30/30 green (findings are physical-validity, not red). Marked tick live (d4e31aa).
- [tick 5 | BUILD] Thought: §3.2 FIX → re-enter BUILD on feat/S1, fix the 6 open_findings via TDD, NO re-research (Muda guard). → Action(spawn general-purpose Generator on feat/S1: resolve a real visible ISS pass + fail-closed altitude Poka-Yoke (F1+F2), widen cone ≥2.1° (F3), single-fixture cleanup + config-matched path (F4), dec-only mangle (F5), confirm F6 rejected; re-fetch + re-commit) → Observation: Generator DONE — 2 commits (RED 11 tests 3700ec3, GREEN impl c2b7bb1); obs_utc→2026-06-17T08:36:12Z (ISS alt 73.1° over Perth, 0.49 d from epoch), center (133.86,-42.59), cone 2.1°/8821 stars, single fixture set. INDEPENDENTLY VERIFIED by parent: 41/41 green, skyfield re-propagation gives ISS alt 73.14° + |obs-epoch| 0.49 d, scope clean, sealed-truth clean.
- [tick 5 | REVIEW] Thought: a FIX must clear a fresh adversarial RE-review before merge. → Action(spawn general-purpose reviewer over `git diff main..feat/S1`) → Observation: VERDICT ACCEPT. All 6 prior findings independently re-verified FIXED (F1 alt-Poka-Yoke fails closed @20° + below-horizon test raises, F2 |obs-epoch|<1d gate, F3 corners covered via real TAN-WCS projection, F4 single fixture + config-matched path, F5 dec-only mangle, F6 rejected); no new BLOCKER/MAJOR (1 NIT: filename 3dp rounding — REJECTED w/ rationale, benign under single-fixture); determinism holds (pointing from fixed config utc; now() only in provenance), sealed-truth intact, tests honest (mutation-probed). 41/41 green.
- [tick 5 | INTEGRATE] Thought: gate passed (all dispositioned + suite green) → integrate. → Action(merge --no-ff feat/S1→main; pytest; delete feat/S1) → Observation: merged @ 274624f; 41/41 non-solver green on main; branch deleted. S1 ≠ a milestone → no tag. no_progress_count 1→0 (green increment landed).
- [tick 5 | HANSEI] What worked: the bounce was FULLY RECOVERED in ONE FIX tick — the Generator fixed all 6 findings, a fresh RE-review ACCEPTed, and an independent skyfield check confirmed the ISS is now at +73.14° (was −84.7°). The loop's bounce→fix→re-review cycle did exactly its job: a real physical-validity defect was caught (tick 4), fixed + verified (tick 5), never papered over, never merged on the incoherent scene. Muda avoided: did NOT re-run research/ideation for the fix (§3.2 guard) — straight to BUILD on the same branch. KAIZEN (S2): render is the FIRST sealed-truth writer + the most complex module — at the S2 PLAN tick JUDGE whether its design content (TAN WCS / PSF / streak / noise / seal boundary) warrants a brief design brief vs a pure SKIP, and build to the seal (truth.json written only by render; image.fits WCS-free) from the first commit. Anti-spin: green merge → no_progress reset to 0.

- [tick 6 | GENBA] Thought: status FRESH, next rung S2 (render); verify gates + re-read the plan's render contract / seal / WCS-pitfalls / Sprint-2 before planning. → Action(Read state; Read plan §contracts+seal+WCS + Sprint 2; git/plan-SHA/baseline) → Observation: on main @ b2cda6a (expected post-S1 bookkeeping commit), clean, no feat/* branches (S1 merged+deleted), plan SHA matches d7237cdd…, baseline 41/41 green. S2 contract + ACs 2.1-2.5 re-grounded.
- [tick 6 | RESEARCH] Thought: S2 (render) is pure construction over the FROZEN S1 fixtures (committed TLE + Gaia CSV) — no dataset/API/algorithm unknown; every primitive is named in the plan (astropy WCS/fits, skyfield radec, numpy default_rng). → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical; S2 settled by the approved plan + frozen fixtures).
- [tick 6 | IDEATE] Thought: render is the KEYSTONE module + the FIRST sealed-truth writer — a BRIEF design brief (nemawashi) pinning the seal boundary + WCS conventions is the right weight (not a full brainstorm — Sprint 2 is fully specified; not a bare skip — the seal is load-bearing). → Action(emit BRIEF design brief, below) → Observation: brief recorded; Pre-Mortem guard clear (render implements its own stub; render IS the sole truth writer + image.fits WCS-free = the seal done right; all signed contracts preserved; no speculative scope).
- [tick 6 | PLAN] Thought: JIT shortcut — S2 fully covered by the approved plan (Sprint 2, ACs 2.1-2.5); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; write the S2 BUILD next_action) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S2 BUILD is the next tick. no_progress stays 0 (plan-lock = progress, §3.3).

### increment design brief (tick 6)

```
S2 — render (synthetic scene + SEALED truth). Build EXACTLY Sprint 2 of the approved plan (ACs 2.1-2.5).
render is the KEYSTONE module: the data-flow hinge (scene -> render -> image.fits CLEAN + truth.json SEALED ->
[solve, detect] -> measure -> score) AND the FIRST + SOLE writer of sealed truth. This is why the S2 BUILD is
high-risk and its review gets a mandatory second local pass.

CHOSEN APPROACH: implement render_scene(scene, catalogue, tle) -> RenderResult on the existing stub. Build a
synthetic astropy WCS (RA---TAN/DEC--TAN, crpix at frame center, NEGATIVE CD1_1 so RA increases left, pixel
scale from the camera model). Project the frozen Gaia stars via wcs.wcs_world2pix(ra, dec, 0) (origin=0 for
numpy arrays) -> Gaussian PSF (sigma ~1-2 px) scaled by phot_g_mean_mag. Propagate the frozen ISS TLE via
skyfield (sat - wgs84.latlon(observer)).at(t).radec() (ICRS, no epoch arg -> ICRS astrometric = the SAME frame
the blind solver's WCS reports, so truth and measured share a frame — airtight non-circularity) at exposure
START / MIDPOINT / END -> pixel endpoints + midpoint -> antialiased streak. Add deterministic Poisson + Gaussian
read noise via numpy default_rng(seed).

THE SEAL (load-bearing — this is why S2 is high-risk):
  - render writes image.fits with NO WCS header — assert the header has NO CRVAL/CD*/CTYPE keywords (clean-FITS
    Poka-Yoke; the formal seal test is S7 but BUILD TO IT HERE).
  - render is the SOLE writer of truth.json (sealed): true WCS params, sat RA/Dec at MIDPOINT (scored truth
    point) + start/end, sat pixel endpoints + midpoint, exposure window, seed, catalogue ref.
  - the 3 solving modules' signatures stay untouched (image_path / wcs only) — they never see truth.

WCS PITFALLS (each gets a round-trip world2pix<->pix2world unit test, AC 2.4): negative CD1_1; origin=0; FITS
row-0-is-bottom vs imshow-top Y-flip (index img[y, x]); RA---TAN/DEC--TAN projection. Scored-point convention
(locks measure<->truth, AC 2.5): truth = sat RA/Dec at exposure MIDPOINT; the streak midpoint is what
measure_position will recover and score will compare against.

TOUCHED MODULES: src/tracklet/render.py (implement stub) + tests/test_render.py (new). out/ artifacts are
runtime-generated + gitignored. scene/solve_pointing/detect_streak/measure_position/score/report/run UNTOUCHED.
Consumes the frozen S1 fixtures (data/) + SceneConfig (S1) OFFLINE (no network in render).

TEST ORACLE (ACs 2.1-2.5, all offline): 2.1 same seed -> identical array hash (same platform + locked versions;
cross-platform portability is the residual threshold, NOT bit-identical bytes — float PSF rendering isn't
bit-stable across arch); 2.2 image.fits header has NO WCS keywords; 2.3 truth.json holds the injected truth;
2.4 WCS round-trip world2pix<->pix2world within sub-px (Y-flip / CD-sign / origin guarded); 2.5 streak endpoints
match the propagated geometry (test MAY read truth). Reuse: astropy.wcs.WCS + astropy.io.fits, skyfield
EarthSatellite/wgs84/timescale, numpy.random.default_rng — do NOT reinvent.

YAGNI / OUT OF SCOPE: NO solve/detect/measure/score (S3-S5); NO report/overlay (S6); NO real image (S8); NO
golden e2e (S7). Render + sealed truth ONLY.

JUDGE: N/A — brief design brief (no design fork; Sprint 2 fully specified). Pre-Mortem guard manual, all four
clear: (a) implements the render stub (re-invents nothing); (b) render IS the sole truth writer + image.fits
WCS-free — the seal done correctly, not broken; (c) all signed module contracts preserved (render_scene
signature per the contract table); (d) scope == Sprint 2 verbatim.
```

- [tick 7 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S2 (keystone); verify PHASE-4 gates + baseline before building. → Action(Read state; git branch/HEAD/clean + commits since 274624f; plan SHA; baseline pytest) → Observation: clean tree @ f6f415b, only loop-authored commits since S1-green, no feat/* branches, plan SHA matches d7237cdd…, baseline 41/41 green. Cut feat/S2.
- [tick 7 | BUILD] Thought: build the render keystone under TDD via a spawned Generator (parent stays lean), TO THE SEAL. → Action(spawn general-purpose Generator on feat/S2: render_scene — synthetic TAN WCS neg-CD1_1, Gaia Gaussian-PSF stars, Skyfield streak start/mid/end (truth=midpoint), deterministic Poisson+read noise, image.fits WCS-FREE + truth.json sole-writer; ACs 2.1-2.5) → Observation: Generator DONE — 3 commits (RED 10a9be4, GREEN 45d66f5, refactor 2223134); 60/60 (41 baseline + 19 render). INDEPENDENTLY VERIFIED by parent: image.fits WCS-free (raw header = only SIMPLE/BITPIX/NAXIS*/EXTEND/BUNIT/TELESCOP), truth.json sole writer = render.py:345, midpoint px (1023.50,1023.50)=frame center, scope clean (render.py + test_render.py only).
- [tick 7 | REVIEW] Thought: S2 HIGH-RISK (sealed-truth write path + WCS math) → MANDATORY 2nd independent LOCAL review. → Action(spawn general-purpose reviewer over `git diff main..feat/S2`) → Observation: VERDICT ACCEPT. Seal holds (raw-header WCS-free, render sole writer, solving sigs byte-identical to main → non-circularity SURVIVES); WCS provably correct (reviewer's OWN off-center flux-centroid residual 0.03px over 30 stars; E→smaller-x, N→larger-y; round-trip tests non-tautological); streak geometry independently re-propagated runs through bright flux; determinism mutation-proven (no now()/global rng); 5/5 test-honesty mutations caught; 60 green. 2 NITs: (a) catalogue_ref re-glob → REJECTED (harmless); (b) streak peak ~162k e ≫ _STREAK_PEAK_E=8e3 (constant misleading) + a bright streak may perturb solve-field → REJECTED for S2 (no AC impact; streak bright + on-line) + CARRIED as an S3 watch-item (plan Sprint 3 mitigations).
- [tick 7 | INTEGRATE] Thought: gate passed (ACCEPT + all dispositioned + green) → integrate. → Action(merge --no-ff feat/S2→main; pytest; delete feat/S2) → Observation: merged @ 6815c32; 60/60 non-solver green on main; branch deleted. S2 ≠ a milestone (M0 needs S0-S7) → no tag. no_progress_count stays 0 (green increment landed).
- [tick 7 | HANSEI] What worked: the KEYSTONE landed clean in ONE tick — the spawned Generator (~123K tok build, compact report to the parent) + a rigorous MANDATORY 2nd review that VERIFIED the seal + WCS by its OWN computation. The off-center flux-centroid residual of 0.03px is the strongest possible evidence there is no CD-sign / Y-flip bug — exactly the WCS-pitfall class the plan flagged. The sealed-truth proof's foundation is now ADVERSARIALLY CONFIRMED, not asserted. KAIZEN (S3): the rendered streak is very bright (~162k e) and the _STREAK_PEAK_E=8e3 constant misdescribes it — S3's AC 3.1 (a REAL blind solve on the actual streaked golden frame) is the empirical test of whether that brightness perturbs solve-field's internal source extraction; if it does, cap the streak peak in render.py (+ make the constant honest) and/or --downsample, then coarse hint, then ASTAP, per plan Sprint 3. Carried in next_action + the post-S2 note so the S3 tick cannot lose it. Anti-spin: green merge → no_progress reset to 0.
