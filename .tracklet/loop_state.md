---
current_milestone: M0
current_increment: "S4 detect_streak (Canny+Hough -> midpoint)"
last_increment_id: "S3 solve_pointing (blind plate-solve)"
phase: BUILD
status: PLAN_LOCKED_AWAITING_BUILD
last_green_sha: a4663ab2cd2ed4d2113455909d9b8c1ade63d80b
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 62, failed: 0}
  - {cmd: 'pytest -m solver', passed: 2, failed: 0, note: 'AC 3.1 blind solve recovered-vs-true 2.0 arcsec worst (tol 10); AC 3.2 SolveFailure on noise frame'}
plan_file: ~/.claude/plans/lucky-dazzling-parasol.md
plan_sha256: d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07
no_progress_count: 0
open_findings: []  # S3 review (mandatory 2nd pass) ACCEPT_WITH_NOTES @ tick 9; 1 MINOR (malformed scale_hint raises KeyError, not SolveFailure) rejected-for-S3 + CARRIED as an S6 run.py watch-item (see post-S3 note)
next_action: >-
  BUILD S4 (Sprint 4: detect_streak — Canny+Hough -> streak midpoint) — the locked design brief is at the bottom
  of this file (tick 10). Cut feat/S4 off main. Implement src/tracklet/detect_streak.py
  detect_streak(image_path) -> StreakDetection|DetectFailure via /tdd-harness or a spawned Generator: load
  image.fits -> sigma-clip bg subtract -> cv2.Canny -> cv2.HoughLinesP -> merge collinear fragments into ONE
  streak -> midpoint of the merged line, refined transversely by a 1D-GAUSSIAN fit to the PERPENDICULAR profile
  (NOT a 2D centroid); DetectFailure (not exception) if none; reads NO truth, signature image_path ONLY.
  Non-solver ACs 4.1-4.4 (all run with ~/tracklet/.venv/bin/python): 4.1 detected midpoint within N px of the
  truth streak midpoint (render golden frame, read truth.json satellite_px mid); 4.2 merges fragments to ONE
  streak; 4.3 DetectFailure on a star-only/streak-absent frame; 4.4 signature has no truth path. The streak now
  renders ~90sigma above noise (S3 mitigation) so it is cleanly detectable. S4 is NOT @solver + NOT high-risk
  (no truth, no WCS math, not a milestone) -> a single thorough local review (PHASE 5) unless the diff is
  >~300 LOC / >8 files; do NOT touch render.py. Merge feat/S4 -> main on green + all findings dispositioned.
human_gate: false
tick_lock: {pid: 10785, started: 2026-06-17T12:08:35Z}  # tick 11 — S4 BUILD live

# --- post-S4-plan note (read before the S4 BUILD tick's §3.5 gate) ---
# S4 plan LOCKED this tick (FRESH -> PLAN_LOCKED_AWAITING_BUILD), JIT shortcut on the approved plan (SHA
# unchanged). main HEAD is now the S4 plan-lock commit, loop-authored commits past last_green_sha a4663ab (S3) —
# expected, NOT a §3.5 anomaly. S4 BUILD tick: assert tree clean + only loop-authored commits since a4663ab, then
# cut feat/S4 off main. S4 is detect_streak (CV): NOT @solver, NOT high-risk (reads no truth, no WCS math, not a
# milestone) -> a single thorough local PHASE-5 review unless the diff is large; do NOT touch render.py.
# Pipeline status: render (S2) + solve_pointing (S3) proven; the rendered streak is ~90sigma above noise so S4
# detection is well-posed. CARRIED S6 WATCH-ITEM (still open): solve_pointing raises KeyError (not SolveFailure)
# on a malformed scale_hint — address when S6's run.py wires real callers. @solver suite (2 tests) must stay green.
# venv ~/tracklet/.venv (Python 3.14.4); cv2/scikit-image/photutils/scipy installed at S0.
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

- [tick 8 | GENBA] Thought: status FRESH, next rung S3 (solve_pointing); verify gates + re-read plan Sprint 3 before planning. → Action(Read state; Read plan Sprint 3 ACs 3.1-3.3; git/plan-SHA/baseline) → Observation: on main @ 2c98859 (S2 bookkeeping), clean, no feat/* branches, plan SHA matches d7237cdd…, baseline 60/60 green. Sprint 3 re-grounded (blind solve-field, SolveFailure-not-exception, @solver AC 3.1 de-risk gated HERE not S7).
- [tick 8 | RESEARCH] Thought: solve-field + 4100 indexes were installed + smoke-verified at S0; the only unknown (does the bright streak perturb the blind solve?) is EMPIRICAL — resolved by running AC 3.1 in the BUILD, not /deep-research. → Action(none — JIT SKIP) → Observation: research SKIPPED (externals installed at S0; de-risk is the @solver build test).
- [tick 8 | IDEATE] Thought: solve_pointing is fully specified (Sprint 3) but consequential (WCS/plate-solve, @solver, carries the streak-brightness watch-item) → a BRIEF design brief pinning the contract + the gated mitigation ladder, not a full brainstorm. → Action(emit BRIEF design brief, below) → Observation: brief recorded; Pre-Mortem clear (implements stub; reads no truth + blind solve → sealed-truth/non-circularity preserved; contract signature preserved; scope == Sprint 3, the render-brightness cap is the plan's OWN gated mitigation not new scope).
- [tick 8 | PLAN] Thought: JIT shortcut — S3 fully covered by the approved plan (Sprint 3, ACs 3.1-3.3); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; write S3 BUILD next_action) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S3 BUILD is the next tick. no_progress stays 0 (plan-lock = progress).

### increment design brief (tick 8)

```
S3 — solve_pointing (blind plate-solve). Build EXACTLY Sprint 3 of the approved plan (ACs 3.1-3.3).
solve_pointing is the FIRST @solver increment and HIGH-RISK (WCS / plate-solve path).

CHOSEN APPROACH: implement solve_pointing(image_path, scale_hint) -> SolveResult | SolveFailure on the stub.
Headless BLIND solve-field: --scale-units degwidth --scale-low/high (from the camera model: fov_deg ± margin),
--downsample 2 --no-plots --overwrite, NO --ra/--dec seed (even the known pointing is NOT fed in → airtight
non-circularity). Parse the produced .wcs with astropy.wcs.WCS. Return a typed SolveFailure (NOT an exception)
on no-solve. Reads NO truth — signature is (image_path, scale_hint) only (AC 3.3). Uses the S0 astrometry.cfg +
4100 indexes (solve-field is local; no network).

THE @solver DE-RISK (AC 3.1, gated EARLY here, not deferred to S7): render the golden scene via S2's
render_scene -> image.fits (the delivered COMPOSITED frame, streak INCLUDED — the clean-FITS seal means there is
only one frame; solving a star-only layer would be cheating), run a REAL blind solve, parse the WCS, assert the
recovered WCS matches the TRUE WCS (from truth.json — the solver-SUCCESS test MAY read truth) within tolerance.
CARRIED WATCH-ITEM (from the S2 review): the rendered streak peak is ~162k e (very bright) and render.py's
_STREAK_PEAK_E=8e3 constant misdescribes it; solve-field runs its OWN source extraction and a bright/saturated
streak CAN spawn spurious detections. So AC 3.1 is the EMPIRICAL gate: IF the blind solve converges correctly
as-is -> no render change (just make the _STREAK_PEAK_E docstring/constant honest as a tidy). IF the streak
perturbs/blocks the solve -> apply the plan's Sprint-3 mitigations IN ORDER: cap streak peak brightness in
render.py (+ fix the constant) -> --downsample -> coarse pointing hint (camera-pointing, NOT satellite truth) ->
ASTAP. Decide empirically in the BUILD; record which mitigation (if any) was needed.

TOUCHED MODULES: src/tracklet/solve_pointing.py (implement stub) + tests/test_solve_pointing.py (new: @solver
solve-success + @solver honest-failure-on-noise + a non-solver signature test). render.py MAY be touched ONLY if
AC 3.1 needs the brightness cap (the plan's documented mitigation) — if so, RE-VERIFY the seal (capping
brightness keeps truth.json sole-writer + image.fits WCS-free; it only dims the streak) and re-run the S2 render
tests. scene/detect/measure/score/report/run UNTOUCHED. Branch hygiene: feat/S3 is the SOLE core branch (it may
edit solve_pointing + optionally render — one branch, allowed).

DATA FLOW: image.fits (from render, CLEAN/no-WCS) -> solve_pointing -> astropy WCS (recovered, blind). The
recovered WCS feeds measure_position (S5). solve_pointing NEVER reads truth.json.

TEST ORACLE (ACs 3.1-3.3): 3.1 @solver — render golden frame -> blind solve -> recovered WCS ≈ true WCS within
tolerance (reads truth); run with ~/tracklet/.venv/bin/python (solve-field + indexes from S0). 3.2 @solver —
SolveFailure RETURNED (not raised) on a pure-noise frame. 3.3 non-solver — signature takes only image_path +
scale_hint (no truth path); structural check. `pytest -m "not solver"` stays green; the @solver tests RUN in
this build (S0 installed the solver) and are the real proof.

YAGNI / OUT OF SCOPE: NO detection (S4), measure/score (S5), report/run (S6), golden e2e (S7), real image (S8).
Just blind solve + honest failure. NO solver-abstraction layer (one solver; ASTAP = documented manual fallback
only if the astrometry.net path fails).

JUDGE: N/A — brief design brief (Sprint 3 fully specified; no design fork). Pre-Mortem guard manual, all clear:
(a) implements the solve_pointing stub (re-invents nothing); (b) sealed-truth preserved — solve_pointing reads
no truth (signature image+hint only), blind solve (no pointing seed); (c) signed contract signature preserved;
(d) scope == Sprint 3 verbatim (the render-brightness cap is the plan's OWN gated mitigation, not new scope).
```

- [tick 9 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S3 (first @solver); verify gates + solver liveness + baseline before building. → Action(Read state; git branch/HEAD/clean + commits since 6815c32; plan SHA; which solve-field + index count; baseline) → Observation: clean tree @ 2719565, only loop-authored commits since S2-green, no feat/* branches, plan SHA matches d7237cdd…, solve-field present + 7 indexes, baseline 60/60 green. Cut feat/S3.
- [tick 9 | BUILD] Thought: build solve_pointing under TDD via a spawned Generator (parent lean); AC 3.1 is the empirical de-risk of the bright streak. → Action(spawn general-purpose Generator on feat/S3: blind solve-field, SolveFailure-not-exception, reads-no-truth; @solver AC 3.1 render+real-blind-solve, 3.2 noise-failure, 3.3 signature) → Observation: Generator DONE — 1 commit cf8de5e; AC 3.1 INITIALLY FAILED (the empirical gate FIRED): streak rendered ~1.7e5 e/px (constant misdescribed it ~20×) + zeropoint left stars near the noise floor → solve-field deblended the bright trail into spurious collinear sources that starved the true-star asterism. Mitigation #1 applied (rewrote _render_streak to a controlled ridge, _STREAK_PEAK_E 8e3→1500 now EXACT, _FLUX_ZEROPOINT_E 1e5→1e6) → blind solve CONVERGES, recovered-vs-true 0.58" center / 2.02" worst (tol 10), index-4112. INDEPENDENTLY VERIFIED by parent: non-solver 62 + @solver 2 green, image.fits still WCS-free (peak 1819 e), render sole truth writer, solve_pointing blind (no --ra/--dec) + reads no truth.
- [tick 9 | REVIEW] Thought: S3 HIGH-RISK (WCS/plate-solve + @solver + render.py — the keystone — was modified) → MANDATORY 2nd independent LOCAL review that re-renders/re-solves/re-verifies the seal + S2 ACs. → Action(spawn general-purpose reviewer over git diff main..feat/S3) → Observation: VERDICT ACCEPT_WITH_NOTES. Reviewer INDEPENDENTLY re-rendered + blind-solved (2.03" worst, no seed; probed 0.3°-off=813", flipped-CD=10233" → 10" cannot hide a mis-solve); seal survived (raw-header WCS-free, render sole writer); ALL S2 ACs still green incl. determinism (3 renders identical hash) + the midpoint convention (delta 0.06/0.10px = real ISS non-linear motion); _STREAK_PEAK_E now EXACTLY 1500 (measured); streak ~90σ above noise (S4-detectable); 25/30 stars >5σ. 1 MINOR: malformed scale_hint raises KeyError not SolveFailure → REJECTED for S3 (out of contract, no AC) + CARRIED as an S6 run.py watch-item. Non-circularity holds.
- [tick 9 | INTEGRATE] Thought: gate passed (ACCEPT_WITH_NOTES + MINOR dispositioned + both suites green) → integrate. → Action(merge --no-ff feat/S3→main; pytest non-solver + solver; delete feat/S3) → Observation: merged @ a4663ab; 62 non-solver + 2 @solver green on main; branch deleted. S3 ≠ a milestone → no tag. no_progress_count stays 0 (green increment landed).
- [tick 9 | HANSEI] What worked: the EMPIRICAL @solver GATE (AC 3.1) did EXACTLY its job — it surfaced a real, non-obvious physical-realism defect (the render dynamic range was unphysical: a ~170k-e streak + near-noise-floor stars) that NO non-solver test could have caught, because only a REAL blind solve exercises solve-field's own source extraction. The project's CORE technical risk (does the synthetic-from-real-data pipeline actually plate-solve?) is now RETIRED at ~2 arcsec. The render mitigation also fixed a latent S2 brightness defect — a Konnyaku-Stone smoothing of an earlier panel, surfaced by stacking the next one on top. Muda avoided: the Generator went straight to the gated mitigation ladder (no flailing). KAIZEN: (1) S6 — solve_pointing must return SolveFailure (not raise) on a malformed scale_hint when run.py wires real callers (carried, post-S3 note). (2) render.py is now touched by BOTH S2 and S3 — it is stable + sealed, but ANY further render change must re-verify the seal + re-run determinism. Anti-spin: green merge → no_progress reset to 0.

- [tick 10 | GENBA] Thought: status FRESH, next rung S4; the harness flagged S2/S3 files "modified" → CRITICAL to confirm the tree is clean (committed work, not drift) before planning. → Action(Read state; Read plan Sprint 4; git status --porcelain + HEAD + commits since a4663ab; plan SHA; baseline) → Observation: porcelain EMPTY (tree CLEAN — the "modified" notes are the committed S2/S3 work, NOT uncommitted drift; no Andon), HEAD aa786d7, only the S3 bookkeeping commit since a4663ab, no feat/* branches, plan SHA matches d7237cdd…, baseline 62/62 green. Sprint 4 re-grounded.
- [tick 10 | RESEARCH] Thought: S4 is pure CV over the rendered frame; cv2/scikit-image/photutils/scipy installed at S0; no dataset/API/algorithm unknown (the plan names the exact ops). → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical CV; S4 settled by the plan + installed libs).
- [tick 10 | IDEATE] Thought: detect_streak is fully specified (Sprint 4) but has real CV content (Canny/Hough params, fragment merge, 1D-Gaussian transverse fit) → a BRIEF design brief pinning the contract + the transverse-fit invariant, not a full brainstorm. → Action(emit BRIEF design brief, below) → Observation: brief recorded; Pre-Mortem clear (implements stub; reads no truth, image only; contract signature preserved; scope == Sprint 4; 1D-Gaussian-NOT-2D-centroid is the load-bearing correctness point).
- [tick 10 | PLAN] Thought: JIT shortcut — S4 fully covered by the approved plan (Sprint 4, ACs 4.1-4.4); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; write S4 BUILD next_action) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S4 BUILD is the next tick. no_progress stays 0 (plan-lock = progress).

### increment design brief (tick 10)

```
S4 — detect_streak (Canny+Hough -> streak midpoint). Build EXACTLY Sprint 4 of the approved plan (ACs 4.1-4.4).
detect_streak is a CV module — NOT @solver, reads NO truth, no WCS math, NOT a milestone.

CHOSEN APPROACH: implement detect_streak(image_path) -> StreakDetection | DetectFailure on the stub. Pipeline:
load image.fits -> sigma-clip background subtract (e.g. astropy sigma_clipped_stats) -> cv2.Canny edge detect ->
cv2.HoughLinesP -> cluster/merge COLLINEAR fragments into ONE streak (the ISS trail is a single long line; Hough
returns multiple segments along it — merge by angle + perpendicular-offset proximity) -> measured point =
MIDPOINT of the merged line (matches the exposure-midpoint scored truth) -> refine the midpoint TRANSVERSELY by a
1D-GAUSSIAN fit to the PERPENDICULAR intensity profile (sample the image along the streak normal at the midpoint,
fit a 1D Gaussian, take its center for sub-pixel transverse position; photutils.centroids.centroid_1dg or
scipy.optimize.curve_fit — NOT a 2D centroid, which is WRONG for an elongated feature). Return DetectFailure
(typed, NOT exception) if no streak is found.

TOUCHED MODULES: src/tracklet/detect_streak.py (implement stub) + tests/test_detect_streak.py (new). render.py
NOT touched — reuse render_scene's rendered frame as the test input (the streak now ~90sigma above noise after
the S3 mitigation, so it is cleanly detectable). scene/solve_pointing/measure_position/score/report/run UNTOUCHED.

DATA FLOW: image.fits (the delivered composited frame WITH the streak) -> detect_streak -> StreakDetection
(merged endpoints + midpoint pixel). The midpoint PIXEL feeds measure_position (S5), which turns it into RA/Dec
via the recovered WCS. detect_streak reads NO truth (signature image_path only).

TEST ORACLE (ACs 4.1-4.4, all NON-solver — pure CV on the rendered frame):
  4.1 detected midpoint within N px of the TRUTH streak midpoint (test renders the golden frame, runs detect,
      reads truth.json's satellite_px midpoint, asserts |detected - truth_mid| < N px; the test MAY read truth).
  4.2 merges collinear Hough fragments into a SINGLE streak (assert one merged streak, not N raw segments).
  4.3 DetectFailure RETURNED (not raised) on a star-only / streak-absent frame (build a stars+noise fixture with
      no satellite trail — e.g. a render variant or a synthetic stars-only array — assert DetectFailure).
  4.4 signature takes only image_path (no truth path; structural/inspect check).

YAGNI / OUT OF SCOPE: NO measure/score (S5 — detect outputs a PIXEL midpoint only), NO report (S6), NO solving.
detect_streak does CV only.

JUDGE: N/A — brief design brief (Sprint 4 fully specified; no design fork). Pre-Mortem guard manual, all clear:
(a) implements the detect_streak stub (re-invents nothing); (b) sealed-truth preserved — detect reads no truth,
takes image only; (c) signed contract signature preserved (detect_streak(image_path)); (d) scope == Sprint 4.
```
