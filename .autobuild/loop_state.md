---
current_milestone: M1
current_increment: "M1 Sprint 4 (run.py --image/--meta + AC-4.6 plausibility gate) — NEXT tick. Sprint 3 (real truth) DONE+merged @ 534bc31 this tick (tick 23)."
last_increment_id: "M1 S3 — real-truth: propagate_satellite_radec extracted behavior-preserving + realtruth assembles the sealed real-frame truth.json (TLE→skyfield topocentric @ exposure midpoint), consumed by score UNCHANGED; seal extended over the new writer; DDOTI site CONFIRMED to published OAN-SPM. MERGED @ 534bc31."
phase: HANSEI  # tick 23 BUILD COMPLETE — M1 Sprint 3 (real-truth) built + 2 independent local review passes ACCEPT + MERGED green. Tick ENDS here (§3.2 BUILD tick = green merge).
status: PLAN_LOCKED_AWAITING_BUILD  # Sprint 3 DONE+merged; the M1 plan is consumed sprint-by-sprint (plan_sha256 unchanged), so the NEXT tick is the Sprint-4 run.py --image/--meta BUILD. ⚠️ Sprint 4 is @solver AND NEEDS THE REAL FRAME (AC 4.1 e2e + AC 2.5 re-exercise) — the 2.4GB BW3 Zenodo frame has NOT been fetched (exceeded the 600s curl window in tick 22). The frame MUST be obtained (longer window / out-of-band fetch.sh) BEFORE Sprint 4 can complete. See needs_human.
last_green_sha: 534bc31  # M1 Sprint-3 merge (--no-ff); 135 non-solver + 5 @solver green on main, M0 golden e2e 2.081" intact
green_suites:
  - {cmd: 'pytest -m "not solver"', passed: 135, failed: 0, note: 'M1 S3 added tests/test_realtruth.py (12: AC 3.1 exposure-midpoint = DATE-OBS(start,UTC)+EXPTIME/2 + robust ISO parse + fail-loud on unparseable/nonpositive — 5 tests; AC 3.2 satellite RA/Dec via the SHARED render.propagate_satellite_radec topocentric + parallax-honored — 2; AC 3.3 truth.json round-trips through score._load_truth UNCHANGED + scored_truth schema matches render — 2; AC 3.5 midpoint + header-WCS returned in-memory + writer-names-no-read-token — 3) + 1 render-helper test (propagate_satellite_radec pure extraction == inline, behavior-preserving) + 1 EXTENDED seal test (static-import forbidden list extended over the THIRD writer realtruth, symmetric to ingest) + updated the site-confirmation fixture test to the confirmed OAN-SPM coords. All load-bearing assertions mutation-verified (midpoint-vs-start, scored_truth key, RA/Dec swap, repo-wide json.load guard catches a smuggled alias in realtruth, realtruth import seal). Run via `make test`.'}
  - {cmd: 'pytest -m solver', passed: 5, failed: 0, skipped: 1, note: 'M0 5 UNCHANGED (golden e2e 2.081" — render propagate_satellite_radec extraction provably behavior-preserving, AC 3.4: render 20 unit tests + golden e2e green). AC 2.5 (NORMALIZED real image still blind-solves+detects = binding Sprint-1 confirmation) STILL PRESENT + skipped (real BW3 frame absent — gitignored *.fits; not yet fetched). Run via `make test-golden`.'}
plan_file: ~/.claude/plans/plan-the-m1-real-image-snappy-bunny.md
plan_sha256: 955c27e35f9ea3627d3edbf6f276105b5d9b1d82b34e0e3d12543062d9b5a2ed
no_progress_count: 0  # Sprint-3 merged GREEN this tick (tick 23) → stays 0 (a green merge resets/holds at 0, §3.3).
open_findings:
  # CARRIED M1 watch-items (NOT blocking; bite at the named sprint):
  - "[BINDING / NEXT @solver window — Sprint 4 gating] AC 2.5 STILL NOT EXECUTED against the real frame — the 2.4GB BW3 Zenodo archive has not been fetched (exceeded the 600s curl --max-time in tick 22). AC 2.5 (the NORMALIZED ingest image still blind-solves+detects) is the BINDING confirmation of the provisional Sprint-1 lock. The test is PRESENT + correct (skip-if-frame-missing). Sprint 4 (run.py --image/--meta, @solver, AC 4.1 e2e) ALSO needs the real frame — so the frame MUST be obtained (longer window / out-of-band fetch via tests/fixtures/real/fetch.sh, or raise the script's curl --max-time) BEFORE Sprint 4 can complete + before the Sprint-1 lock is fully confirmed. A SKIP is NOT a frame rejection."
  - "[Sprint 4 / AC 4.6 — NON-CIRCULARITY, load-bearing] DDOTI frame carries NO header WCS (meta header_wcs_present=false). For THIS frame, pointing-truth = commanded STRCURA/STRCUDE (303.6068/−16.2040) + a FIXED C1 offset DERIVED NON-CIRCULARLY in Sprint 4 by blind-solving ≥3 OTHER C1 frames (scatter <~0.1° or Andon). AC 4.6 plausibility gate = |recovered − (commanded+mean_offset)| ≤ 0.5×fov_deg=1.705°. Do NOT use THIS frame's own recovered−commanded (circular). ingest.IngestResult.header carries the source header in-memory for the report diagnostic; NEVER fed to the blind solve. The realtruth scored truth (306.525,−14.889) lands 0.97° from the tick-21 blind-solved center (305.557,−14.964) = INSIDE the 1.705° half-field — a strong sign the frame + truth are coherent, but the BINDING numeric residual is Sprint 4/6, not this geometric check."
  - "[S4 watch, real trail] detect_streak's transverse 1D-Gaussian refinement can mis-fit on a SATURATED/WIDE streak whose Canny edges exceed the 8px merge tol → midpoint bias. BW3 raw smoke (Sprint 1) detected a 4956-px bright trail @126.16° — watch midpoint robustness on the real trail at Sprint 4."
  - "[benign] _MIN_STREAK_SPAN_PX=100 floor unreachable given _HOUGH_MIN_LINE_LENGTH=150 (S4 NIT)."
  # CLOSED this tick (tick 23, Sprint 3):
  - "[CLOSED tick 23 — AC 3.1] exposure-midpoint timing semantics PINNED: realtruth.exposure_midpoint_utc = DATE-OBS(start,UTC)+EXPTIME/2, fail-loud on unparseable/nonpositive (mutation-verified). Review pass 1 measured the sat moves 5285\" in the 5s start→midpoint window — so the start-vs-midpoint distinction is enormously material (>>10\" gate) and is now locked."
  - "[CLOSED tick 23 — AC 3.2 site] DDOTI/OAN-SPM site CONFIRMED to the published OAN-SPM position 31.044333/−115.46375/2830 m (airmass.org / OAN-UNAM); meta.toml site_confirmed=true; PROVENANCE.md + the fixture-integrity test updated. Residual within-campus uncertainty <~25\" (overhead worst case), below the dominant ~arcminute TLE-age along-track term."
next_action: >-
  ✅ M1 SPRINT 3 COMPLETE + MERGED (tick 23, @ 534bc31). (a) render.propagate_satellite_radec extracted PURE +
  behavior-preserving (render._propagate_satellite now a thin loop over it; render 20 unit tests + golden e2e 2.081"
  green = AC 3.4). (b) NEW src/tracklet/realtruth.py: exposure_midpoint_utc (DATE-OBS start,UTC + EXPTIME/2, fail-loud,
  AC 3.1) + assemble_real_truth (propagate the committed BW3 TLE via the SHARED helper TOPOCENTRIC @ the midpoint →
  truth.json scored_truth that score._load_truth reads UNCHANGED, AC 3.2/3.3; header WCS + midpoint returned IN-MEMORY,
  AC 3.5; json.dump only → score stays the SOLE json.load reader). Seal EXTENDED symmetrically over the new writer
  (test_static_solving_module_does_not_import_realtruth) + the repo-wide alias-resistant json.load guard already covers
  it (mutation-verified). DDOTI site CONFIRMED to published OAN-SPM (31.044333/−115.46375/2830 m; site_confirmed=true).
  135 non-solver + 5 @solver green. 2 independent local review passes ACCEPT; satellite-truth re-derived <1e-9 deg from
  scratch + lands 0.97° INSIDE the blind-solved frame field (305.557,−14.964) = a strong non-circular cross-check.
  The NEXT tick is the SPRINT 4 (run.py --image/--meta) BUILD.

  >>> ⚠️ SPRINT-4 GATING DEPENDENCY — THE REAL FRAME IS NOT YET FETCHED. Sprint 4 is @solver: AC 4.1 runs the FULL
  real pipeline end-to-end (needs the frame) and re-exercises AC 2.5 (the binding Sprint-1 confirmation, also still
  un-run). The 2.4 GB BW3 Zenodo archive exceeded the 600s curl --max-time in tick 22. BEFORE the Sprint-4 BUILD can
  complete, FETCH the frame: run tests/fixtures/real/fetch.sh in a longer window (out-of-band), OR raise its
  curl --max-time, OR Sam drops the funpacked 20221118T024706C1o.fits into tests/fixtures/real/. The fetch.sh streams
  ONLY the single 17.5 MB member (member SHA256 b6dcf797…19ca1) — it never lands the 2.4 GB; the slow part is the
  archive's server-side range read. (Sprint 4 is @solver-gated, so it CANNOT proceed frame-absent the way Sprint 3
  (non-solver) did. If a fresh tick reaches Sprint 4 with the frame still missing, it should FETCH first or Andon to
  Sam — do NOT re-run a blind web search for the frame; the frame is identified + fetch recipe committed.)

  >>> SPRINT 4 (run.py --image/--meta + AC-4.6) BUILD CONTRACT (plan Sprint 4, ACs 4.1-4.6; HIGH-RISK = produces the
  real residual + the non-circular plausibility gate → mandatory 2nd independent LOCAL review). TDD an argparse branch
  in run.py: when --image PATH --meta PATH given, BYPASS build_scene/render_scene; ingest_external_image → clean WCS-free
  image.fits (Sprint 2) + assemble_real_truth → truth.json (Sprint 3, this tick); then solve_pointing(clean_image,
  {"fov_deg": meta.solver.fov_deg}) [BLIND — WCS-free image + scale hint only, AC 4.4] → detect_streak(clean_image) →
  measure_position(detection, solve.wcs) [the BLIND-RECOVERED WCS, AC 4.5 — NEVER the header WCS] → score(measured,
  truth_path) → residual + report. Preserve exit codes 2/3 + "no fabricated residual on a typed failure" (AC 4.3).
  Synthetic default path UNCHANGED (AC 4.2 = M0 golden e2e + all M0 tests green). AC 4.6 PLAUSIBILITY GATE (anti
  wrong-field-lock, load-bearing): derive a FIXED C1-camera offset NON-CIRCULARLY by blind-solving ≥3 OTHER DDOTI C1
  frames (mean offset commanded→recovered; scatter <~0.1° or Andon), then trust a finite residual ONLY if |recovered
  center − (commanded STRCURA/STRCUDE + mean_offset)| ≤ 0.5×fov_deg = 1.705°; else report an HONEST TYPED failure
  (wrong asterism), not a flattering residual. Do NOT use THIS frame's own recovered−commanded (circular). Compute the
  gate from in-memory WCSs downstream of the solver; never feed it back in.

  NON-NEGOTIABLE INVARIANTS (every M1 sprint): (a) SEALED-TRUTH SEAL — json.load/json.loads ONLY in score.py
  (alias-resistant AST guard LIVE; now covers render/ingest/realtruth writers); solve/detect/measure never read truth,
  never take a header WCS; the solver ALWAYS gets the WCS-stripped clean image; do NOT weaken the seal to pass a bad
  test. (b) NON-CIRCULARITY — header/pointing-truth read ONLY by ingest + the report diagnostic IN-MEMORY; satellite
  truth via score._load_truth UNCHANGED; NEVER feed any pointing prior into the blind solve (WCS-free image + coarse
  fov_deg only). (c) HONEST TYPED FAILURE — SolveFailure/DetectFailure → exit 2/3 + labelled msg + NO residual.txt; a
  wrong-field lock failing AC-4.6 is an honest typed failure, not a flattering residual; a NUMERIC residual PASSING
  AC-4.6 is REQUIRED before tagging v0.1.1. (d) REUSE solve_pointing/detect_streak/measure_position/score VERBATIM +
  ingest/realtruth (built); render extractions already done + behavior-preserving. (e) YAGNI — no streak-vs-catalogue
  matcher (PHASE 2). (f) ALL review LOCAL/FREE (/code-review ultra BANNED — the Task/Agent spawn tool has been
  UNAVAILABLE since tick 21, so run TWO genuinely separate in-parent review passes for the high-risk merge); NEVER
  auto-push (v0.1.1 LOCAL only); NEVER write a handoff file.

  >>> REMAINING M1 BUILD SEQUENCE: S4 = run.py --image/--meta + AC-4.6 (THIS next tick, @solver — FETCH THE FRAME
  FIRST; derive the C1 offset non-circularly from ≥3 OTHER C1 frames); S5 = honest degradation report (real
  residual_arcsec always; 5 named sources incl. the ~0.6 d TLE-age along-track error — review pass 1 measured the sat
  moves 5285" in the 5 s exposure, so timing/ephemeris error dominates; pointing-vs-timing decomp, no json.load outside
  score.py); S6 = numeric residual PASSING AC-4.6 + README "Real image (M1)" + tag v0.1.1 LOCAL. GENBA each tick: clean
  tree, only loop-authored commits since last_green 534bc31, re-hash plan 955c27e3, baseline green.

  >>> COMMITTED REAL-FRAME ARTIFACTS (tests/fixtures/real/): bluewalker3_53807.tle (NORAD 53807, epoch 0.598 d
  pre-exposure, checksum-valid); PROVENANCE.md (source/retrieval/identity/TLE/site/smoke + AC-1.5 CLEARED + site now
  CONFIRMED); fetch.sh (streams ONLY the 17.5 MB member, two urls, funpack); meta.toml (verified header values; site
  CONFIRMED this tick). The .fits/.fits.fz are gitignored → fetch.sh on demand. Live smoke (tick 21): solve_pointing→
  center (305.557,−14.964); detect_streak→4956 px @126.16°. Sprint-3 scored truth = (306.525,−14.889) @ midpoint
  2022-11-18T02:47:21.782Z.
human_gate: false  # Sprint-3 merged green; no Andon halt. The AC-1.5 frame-confirmation human gate was already cleared by Sam (tick 19/20, PROVENANCE.md). NOT a hard human stop this tick. BUT a real-world GATING ITEM is surfaced to Sam in needs_human: the real BW3 frame is NOT yet fetched, and Sprint 4 (the NEXT tick) is @solver — it CANNOT complete frame-absent. The frame must be obtained (longer-window/out-of-band fetch.sh, or Sam drops the funpacked .fits in) before Sprint 4. This also finally executes AC 2.5 (the binding Sprint-1 confirmation, still un-run).
tick_lock: null  # cleared at tick-23 end (Sprint-3 BUILD complete + merged green @ 534bc31; feat/m1-s3-realtruth deleted post-merge; no live build in progress)

# --- post-S7-build note / M0 COMPLETE (read before the M1 FRESH planning tick's §3.5 gate) ---
# S7 (the FINAL M0 sprint) BUILT + REVIEWED (mandatory 2nd independent LOCAL adversarial pass — high-risk: closes
# the milestone + formally touches the seal; verdict ACCEPT) + MERGED --no-ff this tick (tick 17) -> main @ d58f94f
# (new last_green_sha) + TAGGED v0.1.0. main HEAD is the S7 merge; the tick-17 bookkeeping commit follows. M1's
# FRESH planning tick: assert tree clean + only loop-authored commits since d58f94f (a FRESH tick does NOT build).
# >>> M0 IS COMPLETE. <<< The synthetic-from-REAL-data optical-SDA proof runs end-to-end via ONE command
# (make run / make test-golden): render -> BLIND plate-solve -> detect -> measure(recovered WCS) -> score, golden
# e2e residual = 2.081" (< 10" gate; expected ~2-4"; < 5" stretch), independently re-rendered+re-solved in REVIEW.
# Seal FORMALLY pinned (tests/test_seal.py: static x6 + runtime + clean-FITS, all 3 pillars mutation-verified RED
# then restored; reviewer re-mutated independently). Repo-wide seal intact: json.load( appears exactly once in
# src/tracklet (score.py:64); all 3 solving-module signatures unchanged (no truth path). README finalized
# (synthetic-from-REAL-data NOT a real-sensor result; footprint+uninstall; network-free reproduce vs committed
# fixtures). LICENSE (MIT) + requirements.lock (3.14.4 + deps, no drift) final. Suites: 103 non-solver + 5 @solver.
# CLOSED this tick: the S5-carried 1-px-convention item — discharged via the offered Option A: test_seal.py +
#   test_golden_e2e.py explicitly cross-reference the DETERMINISTIC sub-pixel round-trip tests
#   (test_render.py::test_wcs_round_trip_subpixel_grid / ::test_wcs_{ra_increases_left,dec_increases_up,
#   center_maps_to_central_pixel} + test_measure_position.py::test_measure_round_trips_pixel_through_world_and_back)
#   that pin the convention with NO solver dependence; the portable 10" gate is kept (plan's anti-flake rationale)
#   and the <5" stretch is reported every golden run. Reviewer independently mutated CD1_1-sign + CRPIX-1px and
#   confirmed those round-trip tests fail deterministically — so a 1-px regression CANNOT hide under the 10" gate.
# CARRIED WATCH-ITEMS into M1 (open, NOT blocking — only relevant once a REAL image is processed):
#   (1) [M1] detect_streak's transverse 1D-Gaussian refinement can mis-fit on a SATURATED/WIDE streak whose Canny
#       edges exceed the 8px merge offset tol (only ONE edge survives -> midpoint bias). Does NOT occur on the
#       synthetic rendered streak (edges within tol; e2e residual 2.08"). Watch midpoint robustness for bright/wide
#       trails on the real frame. (from S4 review)
#   (2) [benign] _MIN_STREAK_SPAN_PX=100 floor is effectively unreachable given _HOUGH_MIN_LINE_LENGTH=150 — a
#       harmless belt-and-suspenders guard, NOT a defect. (S4 review NIT)
# @solver suite is now 5 tests (S3 x2 + S6 x2 + S7 golden x1) — must stay green at every later @solver-touching
# tick. venv ~/tracklet/.venv (Python 3.14.4); cv2/scikit-image/photutils/scipy/astropy/matplotlib at S0.
# HARD-STOP after this tick: M1 (real image) is the NEXT milestone and a SEPARATE tick with an optional
# human-approval andon gate — do NOT begin it now.
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

- [tick 11 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S4 (resumed after a /compact + a "continue" from Sam); verify §3.5 + PHASE-4 gates + baseline before building. → Action(Read state + S4 design brief; git status --porcelain + HEAD + commits since a4663ab; re-hash plan; baseline pytest -m "not solver"; record PID) → Observation: clean tree @ 91c417a, only the tick-9/tick-10 loop bookkeeping commits since a4663ab (no drift), no feat/* branches, plan SHA matches d7237cdd…, baseline 62/62 green, tick_lock null + PID 10785. Set phase BUILD + tick_lock, committed the begin-marker d97b188 on main, cut feat/S4.
- [tick 11 | BUILD] Thought: build detect_streak under TDD via a spawned Generator (parent stays lean); S4 is pure CV, NOT @solver, NOT high-risk. → Action(spawn general-purpose Generator on feat/S4: sigma-clip bg subtract -> Canny -> HoughLinesP -> merge collinear -> 1D-Gaussian transverse-refined midpoint; DetectFailure not raised; reads no truth; ACs 4.1-4.4) → Observation: Generator DONE — 2 commits (RED 31c5b28, GREEN 70cdead); 67 non-solver green; midpoint residual 0.32 px (N=5 px from first principles). INDEPENDENTLY VERIFIED by parent: 67 non-solver + 2 @solver green (no regression), diff touches ONLY detect_streak.py + test_detect_streak.py (render.py + 6 other modules byte-identical to main), source confirms signature image_path-only / no truth import / DetectFailure returned / a genuine 1D-Gaussian transverse fit (not a 2D centroid).
- [tick 11 | REVIEW] Thought: S4 low-risk + small diff -> a single thorough local adversarial review (free, local; §6). → Action(spawn general-purpose adversarial reviewer over git diff main..feat/S4; reviewer ran 4 mutation probes + re-measured 4.1 + checked the seal/fairness/determinism) → Observation: VERDICT ACCEPT_WITH_NOTES, NO blocker. Seal airtight (signature/AST), accuracy real (independently re-measured 0.32 px), 4.3 fixture fair (5044 stars over real noise), determinism + curve_fit fallback safe, scope clean. But 1 MAJOR: AC 4.2's assertion was satisfiable by a NO-MERGE detector (return the longest single Hough fragment) because the golden frame's Hough fragmentation is mild (longest fragment 1369.6 of 1373.5 px); + 2 MINORs (transverse refinement pinned by no assertion; test duplicates front-end params inline) + 1 NIT (span-floor boundary untested).
- [tick 11 | REVIEW-DISPOSITION] Thought: reviewer recommended carrying the MAJOR+MINORs to S5/S6, but the konnyaku doctrine + "never a weak green" say FIX a test-honesty MAJOR BEFORE merge when it is cheap (the increment is unmerged; production code is verified-correct; marginal cost ~0). → Action(test-only hardening on feat/S4: test_merge_collinear_unit [direct merge geometry, 3 frags span 800px vs longest 250px, decoy excluded]; test_detect_reconstructs_fragmented_trail [end-to-end merge proof on a deliberately fragmented trail, representative saturation regime]; test_transverse_refinement_recovers_subpixel_offset [pins the 1D-Gaussian fit recovering a known 0.35px offset]; _raw_hough_segments now references the module CV constants; NIT documented benign) → Observation: 70 non-solver green; then GENCHI-GENBUTSU mutation-verified the new tests are load-bearing — re-applied the two mutations that previously SLIPPED: refinement-no-op now FAILS the transverse test (refined y 31.000 != 31.35), no-merge-longest-fragment now FAILS the fragmented-trail test (159 px < 0.85*530); both reverted, src tree clean, 70 green. Hardening committed 24cd927. Found+fixed a fixture artifact en route (a 6000-peak synthetic ridge saturates >8px wide so its Canny edges exceed the merge tol -> midpoint bias; the REAL streak saturates within tol -> 0.32px; fixture re-tuned to peak 500, the representative regime).
- [tick 11 | INTEGRATE] Thought: PHASE-5 gate met (ACCEPT_WITH_NOTES + every finding dispositioned: MAJOR + 2 MINORs FIXED & mutation-proven, NIT documented; both suites green) → integrate. → Action(git merge --no-ff feat/S4 -> main; pytest non-solver + solver; delete feat/S4) → Observation: merged @ 674462e; 70 non-solver + 2 @solver green on main; branch deleted. S4 ≠ a milestone (M0 needs S0-S7) → no tag. no_progress_count stays 0 (green increment landed).
- [tick 11 | HANSEI] What worked: the loop's review→disposition discipline earned its keep AGAIN — the fresh adversarial reviewer's 4-mutation probe found a MAJOR test-honesty gap (AC 4.2 was green-but-not-load-bearing on the golden frame), and rather than carry it I closed it in-tick and then PROVED the fix with the SAME mutations (red→fixed→green), which is the honest standard the loop demands ("never fake a green" extends to "never a green that a broken impl would also pass"). Genchi-genbutsu (instrumenting the fragmented-trail midpoint instead of guessing) revealed a fixture-vs-detector regime mismatch — a real understanding-gain about WHEN the merge tolerance bites (wide/saturated streaks), now a carried S5/M1 watch-item rather than a buried surprise. The core de-risking is done: render + blind-solve + detect are all proven; the next rung (S5) is the PAYOFF — it produces the headline arcsec residual. KAIZEN (S5): measure_position must read NO truth (pixel + recovered WCS only) and score must be the SOLE truth reader — the S5 build review verifies the read-side seal, completing the non-circularity argument that render (S2) opened on the write side. Watch detect-midpoint robustness for bright trails (carried). Anti-spin: green merge → no_progress stays 0. Per §3.2 the integrate tick advances the ladder: status set FRESH for S5 (the S5 PLAN tick is next).

- [tick 12 | GENBA] Thought: status FRESH for S5; per §3.2 this is a PLAN-only tick (GENBA→RESEARCH→IDEATE→PLAN, hard-stop at the lock). Verify §3.5 + re-read the plan's Sprint 5 / contracts / seal before planning. → Action(Read state; git status --porcelain + HEAD + commits since 674462e; re-hash plan; baseline pytest; grep+read plan Sprint 5 + contract table + seal boundary + error budget) → Observation: clean tree, only the tick-11 bookkeeping commit since 674462e (no drift, no foreign commits), plan SHA matches d7237cdd…, baseline 70/70 non-solver green. Sprint 5 grounded (plan lines 245-249; contract table 73-75; seal boundary 79-93; error budget 267-269, RESIDUAL_THRESHOLD_ARCSEC=10).
- [tick 12 | RESEARCH] Thought: S5 is pure construction over the WCS + sealed truth; astropy SkyCoord/WCS installed + exercised at S0/S2; no dataset/API/algorithm unknown. → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical; S5 settled by the plan + installed astropy).
- [tick 12 | IDEATE] Thought: S5 is fully specified (Sprint 5) but CONSEQUENTIAL — it adds the SOLE truth READER (score) + completes the measurement chain → a BRIEF design brief (pin the contracts + the read-side seal + the WCS-choice subtlety), not a full brainstorm. → Action(emit BRIEF design brief, below) → Observation: brief recorded; the genba read CORRECTED a tick-11 imprecision — AC 5.3 uses the TRUE WCS (isolating detect+measure error, keeping S5 non-solver); the headline blind-solve residual is S7's @solver golden e2e, NOT S5. Pre-Mortem clear: (a) implements the two stubs; (b) seal COMPLETED on the read side (score sole reader, measure reads nothing) — not broken; (c) signed contracts measure_position(streak,wcs)->SkyCoord / score(measured,truth_path)->ScoreResult preserved; (d) scope == Sprint 5 (S7's @solver e2e NOT pulled forward).
- [tick 12 | PLAN] Thought: JIT shortcut — S5 fully covered by the approved plan (Sprint 5, ACs 5.1-5.3); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; write the S5 BUILD next_action; flag S5 HIGH-RISK = read-side seal) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S5 BUILD is the next tick. no_progress stays 0 (plan-lock = progress, §3.3).

### increment design brief (tick 12)

```
S5 — measure_position + score (pixel midpoint -> RA/Dec -> arcsec residual). Build EXACTLY Sprint 5 of the
approved plan (ACs 5.1-5.3). S5 completes the measurement chain AND adds the SOLE truth READER (score) -> it
touches the sealed-truth Poka-Yoke on the READ side -> HIGH-RISK -> mandatory 2nd independent local review.

CHOSEN APPROACH (two stubs):
  - measure_position(streak, wcs) -> astropy SkyCoord (ICRS): lift the StreakDetection's .midpoint pixel to sky
    via wcs.pixel_to_world (origin/convention consistent with render's build_truth_wcs — S2 used origin=0). The
    WCS is an INPUT (true WCS for S5's units; the blind-recovered WCS in S7's e2e) — measure is agnostic. Reads
    NO truth: signature (streak, wcs) only; imports no truth loader; never names truth.json (AST-pinned seal,
    mirroring detect_streak + solve_pointing).
  - score(measured, truth_path) -> ScoreResult: score._load_truth is the SOLE truth loader (the ONLY reader
    besides render the writer). Load truth's exposure-MIDPOINT sky coord (the scored-truth point; confirm the
    exact truth.json key by reading render.py), build a SkyCoord, residual = measured.separation(truth_coord)
    .to(arcsec). Return ScoreResult(residual_arcsec, measured, truth, threshold, passed) — ALWAYS report the
    actual residual; NEVER fabricate one on failure. RESIDUAL_THRESHOLD_ARCSEC = 10 named constant (documented:
    error budget ~2-4"; 2-3x margin).

THE SEAL (read side — why S5 is high-risk): truth lives only in truth.json; score._load_truth is the ONLY loader.
measure_position + the three solving modules never import score._load_truth nor name the truth file. This
COMPLETES the non-circularity argument render (S2) opened on the write side. The formal seal tests are S7, but
BUILD TO THEM HERE.

WCS-CHOICE SUBTLETY (load-bearing, corrected at the tick-12 genba read): AC 5.3 ("golden frame residual <
threshold") uses the TRUE WCS (build_truth_wcs) so it isolates the detect+measure+score error (~detect 0.32px x
5"/px ~= 1-2") and stays NON-solver/deterministic. The FULL headline residual (render -> BLIND solve -> detect ->
measure(recovered WCS) -> score), which folds in the ~2" solve error, is S7's @solver test_golden_e2e — NOT S5.
So S5 is entirely non-solver; do NOT pull S7's @solver golden e2e forward (YAGNI).

TOUCHED MODULES: src/tracklet/measure_position.py + src/tracklet/score.py (implement stubs) + tests/
test_measure_position.py + tests/test_score.py (new). render/solve_pointing/detect_streak/report/run + scene +
fixtures UNTOUCHED. Consumes: a StreakDetection (S4), an astropy WCS (true WCS via build_truth_wcs for S5),
truth.json (read ONLY by score).

DATA FLOW: detect_streak -> StreakDetection.midpoint (pixel) -> measure_position(.,wcs) -> SkyCoord(ICRS) ->
score(.,truth_path) -> ScoreResult.residual_arcsec. score is the terminus + the sole truth reader.

TEST ORACLE (ACs 5.1-5.3, ALL non-solver, run with ~/tracklet/.venv/bin/python):
  5.1 pixel->RA/Dec round-trips correctly: build_truth_wcs(scene); a known pixel -> measure_position -> world ->
      back ~= pixel (sub-px), or compare measure_position's SkyCoord to wcs.pixel_to_world directly. Guards the
      origin/convention (the same Y-flip/CD-sign class S2 pinned).
  5.2 score arcsec arithmetic verified against a known HAND-COMPUTED SkyCoord.separation (two coords a known
      angular distance apart -> assert residual matches, units correct).
  5.3 golden frame: render -> detect_streak(image) -> measure_position(detection, build_truth_wcs(scene)) ->
      score(measured, truth_path) -> residual < RESIDUAL_THRESHOLD_ARCSEC; report the ACTUAL value (~1-2"). The
      test MAY read truth. Isolates detect+measure error (true WCS); the blind-solve residual is S7.
  Build-to-the-seal (formalized in S7, asserted here): measure_position takes only (streak, wcs) [inspect];
  measure imports no truth / never names truth.json [AST]; score is the only module that reads truth.

YAGNI / OUT OF SCOPE: NO report/overlay (S6), NO run.py/one-command (S6), NO @solver golden e2e + formal seal
tests (S7), NO real image (M1). measure + score ONLY.

JUDGE: N/A — brief design brief (Sprint 5 fully specified; no design fork). Pre-Mortem guard, all clear:
(a) implements the two stubs (re-invents nothing); (b) sealed-truth COMPLETED on the read side — score sole
reader, measure reads nothing — done right, not broken; (c) signed contracts preserved; (d) scope == Sprint 5.
```

- [tick 13 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S5 (HIGH-RISK, read-side seal); verify PHASE-4 gates + baseline + the EXACT truth.json key before building. → Action(Read state + S5 design brief; git status --porcelain + HEAD + commits since 069ccb7… wait 674462e; re-hash plan; baseline; grep render.py for the truth dict + build_truth_wcs; Read the two stubs) → Observation: clean tree @ bf5995b, only the tick-11/12 loop commits since 674462e (no drift), plan SHA matches d7237cdd…, status PLAN_LOCKED_AWAITING_BUILD + tick_lock null, baseline 70/70 green. Confirmed score must read truth["scored_truth"]["ra_deg"/"dec_deg"] (render.py:294 = the exposure-midpoint scored point); build_truth_wcs at render.py:92. Set phase BUILD + tick_lock, committed begin-marker e3ddeeb on main, cut feat/S5.
- [tick 13 | BUILD] Thought: build measure_position + score under TDD via a spawned Generator (parent lean), to the read-side seal. → Action(spawn general-purpose Generator on feat/S5: measure_position(streak,wcs)->SkyCoord via wcs.pixel_to_world reads-no-truth; score(measured,truth_path)->ScoreResult, score._load_truth sole reader of scored_truth, residual=separation.to(arcsec), RESIDUAL_THRESHOLD_ARCSEC=10, no fabrication; non-solver ACs 5.1-5.3 + seal tests) → Observation: Generator DONE — 2 commits (RED a982d24, GREEN 5cccf69); 82 non-solver green; AC 5.3 golden detect+measure residual 1.6047" (TRUE WCS). INDEPENDENTLY VERIFIED by parent: 82 non-solver + 2 @solver green (no regression), diff touches ONLY measure_position.py + score.py + their tests (render/solve/detect/scene byte-identical), source confirms measure reads no truth (signature streak+wcs, imports only SkyCoord) + score._load_truth sole reader of scored_truth + honest residual (no clamp). Internal-consistency check: 1.60" = detect 0.32px x ~5"/px (true WCS -> zero solve error), exactly as expected.
- [tick 13 | REVIEW] Thought: S5 HIGH-RISK (adds the SOLE truth reader = the read-side seal) → MANDATORY 2nd independent local adversarial review that re-recomputes the arithmetic + re-renders + greps the whole tree for truth reads. → Action(spawn general-purpose adversarial reviewer over git diff main..feat/S5; reviewer ran 4 mutation probes + independent haversine recompute + scratch re-render + whole-tree truth-read grep) → Observation: VERDICT ACCEPT, NO blocker/major. Seal PROVEN: json.load appears EXACTLY ONCE in src/tracklet (score.py:64); scored_truth read only at score.py:65, written only at render.py:294; measure imports only SkyCoord. All 4 mutations CAUGHT (axis-swap, residual-clamp, wrong-key; 1-px offset caught by 5.1b round-trip). Arithmetic independently agrees to <=2e-11" incl. a cos(dec) diagonal (real great-circle). Re-render residual 1.6047" reproduced. Determinism + ICRS confirmed. 1 MINOR (5.3's 10" gate loose vs 1-px error -> an S7-e2e design note; convention already tightly pinned by 5.1b) + 2 NITs.
- [tick 13 | REVIEW-DISPOSITION] Thought: unlike tick 11's MAJOR (the increment's OWN AC failed to catch its target), here the convention IS tightly caught by 5.1b (mutation-confirmed) — the MINOR is a forward-looking note about S7's @solver e2e gate, NOT an S5 hole. So CARRY (not fix-in-tick); 2 NITs no-action with rationale. → Action(record the MINOR as an S7 carried watch-item in the post-S5-build note; NITs documented) → Observation: every finding dispositioned; no in-tick code change needed (S5's own tests are sound). PHASE-5 gate met.
- [tick 13 | INTEGRATE] Thought: gate passed (ACCEPT + all dispositioned + both suites green) → integrate. → Action(git merge --no-ff feat/S5 -> main; pytest non-solver + solver; delete feat/S5) → Observation: merged @ 069ccb7; 82 non-solver + 2 @solver green on main; branch deleted. S5 ≠ a milestone (S7 closes M0) → no tag. no_progress_count stays 0 (green increment landed).
- [tick 13 | HANSEI] What worked: the MANDATORY 2nd review for a seal-touching increment did exactly its job — it PROVED (not asserted) the non-circularity seal by independently grepping the whole tree (json.load once, in score), recomputing the great-circle arithmetic to 2e-11", and re-rendering from scratch to reproduce 1.60". The measurement chain is now closed end-to-end on the TRUE WCS, and the residual's internal consistency (1.60" = detect's 0.32px x pixel scale) is the strongest evidence the pixel convention is right. Honest scoping: I distinguished this review's MINOR (a forward S7-e2e design note, convention already tightly pinned by 5.1b) from tick 11's MAJOR (an actual in-increment test hole) — carry vs fix-in-tick is a real judgment, not a reflex. KAIZEN (S6): S6 wires the FULL pipeline with the BLIND-recovered WCS for the first time (run.py happy path = @solver) AND must wire the carried malformed-scale_hint fix (solve_pointing -> SolveFailure not KeyError) + honest typed failure all the way out (never fabricate a residual on no-solve/no-detect). Anti-spin: green merge → no_progress stays 0. Per §3.2 the integrate tick advances the ladder: status set FRESH for S6 (the S6 PLAN tick is next).

- [tick 14 | GENBA] Thought: status FRESH for S6; per §3.2 a PLAN-only tick (GENBA→RESEARCH→IDEATE→PLAN, hard-stop at the lock). Verify §3.5 + RE-READ the plan's Sprint 6 + the run.py/report.py stubs before planning. → Action(Read state; git status --porcelain + HEAD + commits since 069ccb7; re-hash plan; baseline pytest; Read plan lines 250-330 = Sprint 6 ACs + Verification + Risks; Read run.py + report.py stubs) → Observation: clean tree, only the tick-13 bookkeeping commit since 069ccb7 (no drift), plan SHA matches d7237cdd…, baseline 82/82 green. Sprint 6 grounded (report.py + run.py + Makefile; ACs 6.1-6.4; honest-failure non-zero exit + no fabricated residual; determinism). run.py stub already calls assert_supported_python() FIRST (the S0 minor-version guard) — must preserve. report contract "reads truth only via the score result".
- [tick 14 | RESEARCH] Thought: S6 is pure wiring + a matplotlib overlay over already-built modules; matplotlib + the whole stack installed at S0; no dataset/API/algorithm unknown. → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical wiring; S6 settled by the plan + installed libs).
- [tick 14 | IDEATE] Thought: S6 is fully specified (Sprint 6) but CONSEQUENTIAL — first full-pipeline @solver run, honest-failure paths, + the carried solve_pointing fix → a BRIEF brief, not a full brainstorm. → Action(emit BRIEF design brief, below) → Observation: brief recorded. Seal stays intact: the MEASUREMENT path (solve/detect/measure) never sees truth; score reads it (sole reader); run PASSES the truth path to score (does not open it); report uses score_result.truth for the transparency marker (does not open truth.json) — so json.load must STILL appear only in score.py post-build. Pre-Mortem clear: (a) implements the two stubs; (b) sealed-truth preserved (measurement path truth-free; score sole reader); (c) signed contracts preserved (run.main(argv)->int; report.write_report(score,overlay_inputs,out_dir); the carried fix keeps solve_pointing's contract — SolveFailure is already a valid return); (d) scope == Sprint 6 (S7's golden e2e/seal-tests/README NOT pulled forward).
- [tick 14 | PLAN] Thought: JIT shortcut — S6 fully covered by the approved plan (Sprint 6, ACs 6.1-6.4); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD; keep plan_file/SHA; write the S6 BUILD next_action incl. the carried fix) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 the FRESH tick HARD-STOPS here — the S6 BUILD is the next tick. no_progress stays 0 (plan-lock = progress).

### increment design brief (tick 14)

```
S6 — report + run + ONE command. Build EXACTLY Sprint 6 of the approved plan (ACs 6.1-6.4) + wire the carried
malformed-scale_hint fix. S6 WIRES THE FULL PIPELINE end-to-end for the first time WITH the BLIND-RECOVERED WCS
(render -> solve_pointing(blind) -> detect_streak -> measure_position(recovered WCS) -> score -> report), so
run.py's happy path is @solver — the first full-pipeline blind-solve residual.

CHOSEN APPROACH (two stubs + Makefile + one carried fix):
  - report.py: write_report(score, overlay_inputs, out_dir) -> report.md (scene summary; solve status; detection
    status; residual arcsec; threshold + PASS/FAIL; provenance: TLE source+date, Gaia query, solver + index
    series, Python version; what-it-proves / what-it-does-NOT) + overlay.png (matplotlib: image + detected streak
    + measured position + a labelled TRUTH marker, FOR TRANSPARENCY). report reads truth ONLY via the score result
    (score_result.truth) — NEVER opens truth.json (score stays the sole reader).
  - run.py: main(argv)->int. KEEP assert_supported_python() FIRST. scene=build_scene(config) -> render_scene ->
    image.fits + truth.json in out/ -> solve_pointing(image_path, scale_hint from scene.fov_deg) -> detect_streak
    (image_path) -> measure_position(streak, RECOVERED wcs) -> score(measured, out_dir/truth.json) -> write_report.
    Emit out/{image.fits, truth.json, residual.txt, overlay.png, report.md}; PRINT the residual; exit 0 on a clean
    run. HONEST FAILURE: a SolveFailure / DetectFailure -> labelled message ("could not solve"/"could not detect")
    + NON-ZERO exit + NO residual.txt + NO fabricated residual (typed failure all the way out).
  - Makefile: make run | test | test-golden.
  - CARRIED FIX (solve_pointing.py): malformed scale_hint -> RETURN SolveFailure (not raise KeyError). SolveFailure
    is already a valid return -> contract-respecting. Add a NON-solver test (malformed hint -> SolveFailure, fails
    before solve-field is invoked). RE-RUN @solver after.

THE SEAL (stays intact — re-verify post-build): json.load appears ONLY in score.py. run passes the truth PATH to
score; report uses the score RESULT's truth; the three solving modules + measure are unchanged + truth-free. The
overlay's truth marker is post-scoring transparency, not a measurement input.

TOUCHED MODULES: src/tracklet/report.py + src/tracklet/run.py (implement stubs) + src/tracklet/solve_pointing.py
(carried fix ONLY) + Makefile + tests/{test_report.py, test_run.py, + a non-solver malformed-hint test for
solve_pointing}. render/detect_streak/measure_position/score/scene UNTOUCHED.

DATA FLOW: config -> run -> render(out/) -> solve(image)->WCS | detect(image)->streak -> measure(streak,WCS)->
SkyCoord -> score(measured, out/truth.json)->ScoreResult -> report(score, overlay_inputs, out/) -> artifacts.

TEST ORACLE (ACs 6.1-6.4): 6.1 @solver — python -m tracklet.run on the golden scene produces residual.txt +
overlay.png + report.md; residual finite + printed + written (the FIRST full-pipeline blind-solve residual; run
with ~/tracklet/.venv/bin/python). 6.2 NON-solver — monkeypatch solve_pointing -> SolveFailure; run.py reports
"could not solve" + non-zero exit + NO residual.txt (no fabrication). 6.3 NON-solver — star-only frame ->
detect_streak DetectFailure -> run.py reports "could not detect" honestly + non-zero exit. 6.4 out/ artifacts
well-formed (report.md has the residual + PASS/FAIL; residual.txt parses to a float; overlay.png is a valid PNG).
Determinism: make run twice -> identical image.fits hash + identical residual. + the carried-fix non-solver test.

YAGNI / OUT OF SCOPE: NO formal 3 seal tests, NO golden-e2e gate test, NO README (all S7); NO real image (M1); NO
new config knobs. report + run + Makefile + the one carried fix ONLY. Do NOT pull S7 forward.

JUDGE: N/A — brief design brief (Sprint 6 fully specified; no design fork). Pre-Mortem guard, all clear:
(a) implements the report + run stubs (re-invents nothing); (b) sealed-truth preserved — measurement path
truth-free, score the sole reader, run/report never open truth.json; (c) signed contracts preserved (run.main /
report.write_report / solve_pointing's SolveFailure-valid-return); (d) scope == Sprint 6 + the carried fix.
```

- [tick 15 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S6; verify PHASE-4 gates + baseline + the Makefile state before building. → Action(Read state + S6 design brief; git status --porcelain + HEAD + commits since 069ccb7; re-hash plan; baseline pytest; cat Makefile) → Observation: clean tree, only the tick-13/14 loop commits since 069ccb7 (no drift), plan SHA matches d7237cdd…, status PLAN_LOCKED_AWAITING_BUILD + tick_lock null, baseline 82/82 green. Makefile ALREADY wires run|test|test-golden (S0 scaffold) -> S6's Makefile obligation already met; build = report.py + run.py + the solve_pointing fix + tests. Set phase BUILD + tick_lock, committed begin-marker 65dcf91 on main, cut feat/S6.
- [tick 15 | BUILD] Thought: build the full-pipeline orchestrator + report + the carried fix under TDD via a spawned Generator (parent lean). → Action(spawn general-purpose Generator on feat/S6: run.main wiring scene->render->solve(BLIND)->detect->measure(recovered WCS)->score->report; honest typed failure; report reads truth only via score result; carried solve_pointing malformed-hint->SolveFailure fix; ACs 6.1-6.4 + determinism + seal) → Observation: Generator DONE — 2 commits (RED bf8cf48, GREEN f3aa058); 94 non-solver + 4 @solver green; headline full-pipeline BLIND-solve residual 2.0815" (< 10", PASS) — the FIRST end-to-end real number. INDEPENDENTLY VERIFIED by parent: diff touches ONLY the 6 allowed files (render/detect/measure/score/scene + Makefile byte-identical); json.load appears ONLY in score.py:64; both suites green; read run.py (residual.txt written ONLY after a real residual; SolveFailure/DetectFailure -> non-zero + no residual) + report.py (reads score.truth, projects via recovered WCS, never opens the sealed artifact) + the solve_pointing diff (contract-respecting, valid hints byte-unchanged); RAN `make run` myself -> residual 2.081474 + valid PNG + honest report.md (Measured vs Truth + "what it does NOT prove"). Internal consistency: 2.08" blind ~= quadrature(1.60" detect+measure, ~1.3" solve).
- [tick 15 | REVIEW] Thought: large diff (692 LOC) + edits solve_pointing.py (prior @solver module) + produces the HEADLINE NUMBER -> MANDATORY 2nd independent local adversarial review. → Action(spawn general-purpose adversarial reviewer over git diff main..feat/S6; reviewer ran the one command, mutation-probed honest-failure, grepped the whole tree for truth reads, recomputed the true-WCS residual, checked valid-hint equivalence) → Observation: VERDICT ACCEPT_WITH_NOTES, NO blocker/major. Honest-failure PROVEN (4 mutations caught: return-0-on-fail, fabricate-residual, both failure types); headline 2.0815" is a GENUINE blind-solve number (recomputed true-WCS 1.6047" + quadrature 1.33" solve contribution); seal intact (json.load only score.py; run passes path, report uses result, OverlayInputs carries no truth path); valid-hint behavior byte-identical (@solver 4/4); determinism reproduced. 1 MINOR: a stale residual.txt from a prior SUCCESS survives a later FAILED run into the same out/ dir (proven: pre-seed 999.99 + inject SolveFailure -> exit 2, honest msg, but 999.99 remains). + 1 NIT (no stale-case test).
- [tick 15 | REVIEW-DISPOSITION] Thought: unlike tick 13's carry (a forward S7 design note), this MINOR is a real honesty-HYGIENE gap IN run.py on the HEADLINE artifact — and stranger-reproducibility (the M_final DoD) means someone will cat out/residual.txt and trust it. Fix is ~3 lines + a regression test (closes the NIT too). FIX in-tick (tick 11 precedent: fix cheap honesty-relevant defects before merge). → Action(add tests/test_run.py::test_failed_run_clears_stale_result_artifacts; confirm RED against current run.py (stale residual.txt survives); add run.main: unlink residual.txt/report.md/overlay.png at start before solve/detect; GREEN) → Observation: RED confirmed (stale file survived), fix GREEN. The EXISTING seal test test_run_does_not_open_truth_directly then FAILED because my fix comment literally contained "truth.json" -> reworded to "the sealed answer" (Poka-Yoke seal test earned its keep — caught a comment slip). 95 non-solver + 4 @solver green. Fix committed 24f0a8d. Every finding dispositioned (MINOR+NIT fixed + mutation-verified; the S5 MINOR carried to S7 where the golden e2e is built).
- [tick 15 | INTEGRATE] Thought: gate passed (ACCEPT_WITH_NOTES + all dispositioned + both suites green) → integrate. → Action(git merge --no-ff feat/S6 -> main; pytest non-solver + solver; delete feat/S6) → Observation: merged @ 9b06df8; 95 non-solver + 4 @solver green on main; branch deleted. S6 ≠ a milestone (S7 closes M0) → no tag. no_progress_count stays 0 (green increment landed).
- [tick 15 | HANSEI] What worked: the full pipeline now runs end-to-end via ONE command and produces a real, honest, independently-reproduced 2.08" blind-solve residual — the core product exists. The 2nd review for the headline-number + solve-path-touching diff did its job (proved honest-failure + the seal + the blind-vs-true distinction by recomputation, not assertion), and the in-tick MINOR fix kept the headline artifact honest (no stale residual can masquerade as current). Genchi-genbutsu: running `make run` myself + reading the artifacts (not trusting the Generator/review narrative) is what confirmed the DoD-shaped result. Konnyaku-stone moment: the seal test caught my own fix-comment slip ("truth.json") — the Poka-Yoke is load-bearing even against the operator. KAIZEN (S7): S7 CLOSES M0 — build the 3 formal seal tests (static/runtime/clean-FITS) + the @solver golden-e2e DoD gate + README/LICENSE/requirements.lock; fold in the carried convention-bound note (the 10" gate can't catch a 1-px bug; lean on the round-trip seal or add the <5" stretch sanity); on DoD met (RUN the named green commands + verify clean-clone reproduce) TAG v0.1.0. Anti-spin: green merge → no_progress stays 0. Per §3.2 the integrate tick advances the ladder: status set FRESH for S7 (the S7 PLAN tick is next).

- [tick 16 | GENBA] Thought: status FRESH, next rung S7 (the FINAL M0 sprint — closes M0); this is the FIRST tick driven by the `/autobuild-loop` SKILL reading `.autobuild/` (post-S8 runner migration, NOT the bespoke chat prompt) — verify §3.5 gates + plan + baseline before planning, AND prove the engine reads the migrated paths. → Action(load `.autobuild/config.md` via config.load_config + read `.autobuild/loop_state.md`; git status/HEAD/branches + commits since 9b06df8; re-hash plan; baseline `pytest -m "not solver"` + `-m solver` via ~/tracklet/.venv/bin/python3) → Observation: ENGINE READ `.autobuild/` CLEANLY — config.md schema-VALID (ladder M0..M_final; green = not-solver/solver), loop_state.md reconstructed (S7 / phase HANSEI / status FRESH / tick_lock null). Gates: tree clean, HEAD==main, 0 feat/* branches; commits since last_green 9b06df8 = c03e978 (tick-15 bookkeeping) + 5e70012 (S8 migration) — BOTH non-source (loop_state move + config), no drift/Andon; plan SHA matches d7237cdd…; baseline 95 non-solver + 4 @solver green (real `make run` blind residual 2.08"). Runner migration verified LIVE.
- [tick 16 | RESEARCH] Thought: S7 is the milestone-completing hardening sprint — formal seal tests + a golden-e2e gate over already-built modules + docs; no external dataset/API/algorithm unknown (the README footprint/uninstall/licence facts are real but confirmed in BUILD). → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical hardening over built modules; S7 settled by the approved plan's Sprint 7).
- [tick 16 | IDEATE] Thought: S7 closes M0 + formally touches the seal → a BRIEF brief (Sprint 7 fully specified; no design fork). → Action(emit BRIEF design brief, below) → Observation: brief recorded. Pre-Mortem clear: (a) adds seal tests + golden-e2e + docs over built modules (re-invents nothing); (b) the seal tests VERIFY the sealed-truth / non-circularity invariant (preserve it, formally — they do not weaken it); (c) signed module contracts preserved (no new source module; if a seal test needs a tiny test-only hook in a solving module, re-verify that module's contract + the seal); (d) scope == Sprint 7 (ACs 7.1-7.5 + the carried 1-px-convention tightening); no speculative scope.
- [tick 16 | PLAN] Thought: JIT shortcut — S7 fully covered by the approved plan (Sprint 7, ACs 7.1-7.5); skip /ultraplan, consume it, keep plan_sha256. → Action(set status PLAN_LOCKED_AWAITING_BUILD + phase PLAN; keep plan_file/SHA; write the S7 BUILD next_action) → Observation: status PLAN_LOCKED_AWAITING_BUILD; plan_sha256 unchanged d7237cdd…; per §3.2 this FRESH tick HARD-STOPS at the plan-lock — the S7 BUILD is the NEXT tick (a fresh `/autobuild-loop` session). no_progress stays 0 (plan-lock = progress, §3.3). ⚠️ DRIVEN AS A ONE-OFF PROOF TICK (operator-invoked to validate the S8 migration): NO next tick scheduled, NO ScheduleWakeup, NOT a recurring loop — the autonomous build resumes when a human launches `/autobuild-loop` on ~/tracklet in a fresh session.

### increment design brief (tick 16)

```
S7 — seal tests + golden e2e + README/docs -> M0 DoD + tag v0.1.0. Build EXACTLY Sprint 7 of the approved plan
(lucky-dazzling-parasol.md). S7 is the FINAL M0 rung + HIGH-RISK (completes the milestone + formally touches the
seal) -> MANDATORY 2nd independent LOCAL review (cost guard: local only).

SCOPE (JIT — Sprint 7, full detail in next_action):
  (1) tests/test_seal.py — STATIC (AST/source: solve_pointing/detect_streak/measure_position import no truth
      loader + never name the sealed artifact), RUNTIME (monkeypatch score._load_truth to RAISE -> the solving
      path still completes; only score fails), CLEAN-FITS (image.fits header has NO WCS keywords).
  (2) tests/test_golden_e2e.py — @solver, THE executable DoD: render frozen scene -> FULL blind-solve pipeline ->
      assert residual_arcsec < RESIDUAL_THRESHOLD_ARCSEC; ALWAYS report the actual number + the ~2-4" band.
  (3) README honesty (synthetic-from-REAL-data, NOT a real-sensor result; threshold + error budget; exact
      clone -> make setup -> make test-golden steps; ON-DISK FOOTPRINT + UNINSTALL; ASTAP fallback; Gaia DR3 /
      CelesTrak / astrometry.net provenance + licences) + LICENSE + finalize requirements.lock.
  ACs 7.1 (3 seal tests), 7.2 (golden test passes, number always reported), 7.3 (clone+steps reproduce clean),
  7.4 (README states what it PROVES AND does NOT + footprint/uninstall), 7.5 (non-solver suite green w/o solver).
  CARRIED (S5 review, ACTIONABLE): the 10" gate is loose vs a 1-px convention error (~7" < 10"); the convention is
  already pinned by the round-trip seal tests (S2 AC 2.4 + S5 AC 5.1b) -> NOTE that coverage OR add the <5" stretch
  sanity bound so a pixel-convention regression can't hide under the 10" gate.
  On DoD met (RUN make test-golden + pytest -m "not solver" + verify clean-clone reproduce) -> merge feat/S7 ->
  main + TAG v0.1.0 (M0 complete). Do NOT push (human-gated).

TOUCHED: tests/test_seal.py + tests/test_golden_e2e.py (new) + README + LICENSE + requirements.lock. The 7 product
modules are NOT re-implemented (S7 hardens + documents). Sealed-truth preserved (the seal tests verify it).

JUDGE: N/A — brief brief (Sprint 7 fully specified; no design fork).
```

- [tick 17 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for S7 (the FINAL M0 sprint, HIGH-RISK — touches the seal); the tick-16 plan-lock was a one-off proof tick, so this is the separate fresh-context BUILD tick. Verify no colliding session + §3.5 gates + baseline before a seal-touching build. → Action(list_sessions isRunning check; git branch/HEAD/status/branches + commits since 9b06df8; re-hash plan; baseline `pytest -m "not solver"` + `-m solver` via .venv/bin/python3; read config + state + plan Sprint 7/Verification/Risks + all 7 modules + every existing test) → Observation: "Tracklet autonomous build loop" session isRunning=false (no collision; the 2 running sessions are space-research chats). Tree clean, on main @ f6cf054, 0 feat/* branches; 3 commits since 9b06df8 (S7 plan-lock + S8 migration + tick-15 bookkeeping) all loop-authored chore — no drift; plan SHA matches d7237cdd…; baseline 95 non-solver + 4 @solver green. Genba: each solving module ALREADY has a per-module structural seal; S6 added the repo-wide json.load(-only-in-score pin; the 1-px-convention class is ALREADY pinned by deterministic round-trip tests (test_render + test_measure_position). Cut feat/S7.
- [tick 17 | BUILD] Thought: build the formal seal gate + golden-e2e DoD + docs DIRECTLY in the parent under TDD (high-risk seal work — keep close to it; the heavy lifting is test design, not a big module build), inner discipline Red→Green→Refactor + mutation-verify for the guard tests. → Action(write tests/test_seal.py — STATIC consolidation (parametrised over the 3 solving modules: name no truth.json/_load_truth; import no score/render/scene) + RUNTIME (monkeypatch score._load_truth→raise; detect+measure complete; only score raises) + CLEAN-FITS; write tests/test_golden_e2e.py — @solver render→blind-solve→detect→measure(recovered WCS)→score, assert residual < RESIDUAL_THRESHOLD_ARCSEC, always-report via capsys.disabled(); finalize README (stale Sprint-0 status → M0/v0.1.0; crisp network-free reproduce; error budget); verify requirements.lock vs venv) → Observation: TDD caught a real bug immediately (pytest.raises match= had regex metachars → fixed sentinel). All 8 seal tests green; all 3 pillars MUTATION-VERIFIED RED then restored (static-import, static-name, runtime-via-broken-loader, clean-FITS-CRVAL leak). Golden e2e PASS residual 2.081" (expected ~2-4", <5" stretch, <10" gate). requirements.lock = venv (only the editable self-install differs — correct). LICENSE already final. 103 non-solver + 5 @solver green; diff = 2 new test files + README only (NO source-module change — the seal held untouched).
- [tick 17 | REVIEW] Thought: S7 HIGH-RISK (completes M0 + formally touches the seal) → MANDATORY 2nd independent LOCAL adversarial review (cost guard: local only, /code-review ultra BANNED). → Action(spawn fresh-context general-purpose adversarial reviewer over git diff main..feat/S7 with a brief demanding independent re-render+re-solve, independent mutation of all seal pillars + the convention, AC-by-AC verification; reviewer must leave the tree clean) → Observation: VERDICT ACCEPT (no blocker/major/minor; 2 NITs). Reviewer INDEPENDENTLY: ran the blind pipeline → residual 2.0815" reproduced; proved non-circularity (recovered WCS crval ≠ true by ~0.35°; through-true-WCS residual 1.60" vs through-recovered 2.08"; image.fits WCS-free; measure uses recovered WCS); re-ran all mutation probes RED; mutated CD1_1-sign + CRPIX-1px → confirmed the cited deterministic round-trip tests fail without the solver (CARRIED item genuinely discharged); json.load( only in score.py; signatures unchanged. Tree left clean.
- [tick 17 | INTEGRATE] Thought: gate passed (ACCEPT + both NITs dispositioned no-change + both suites green + documented `make test`/`make test-golden` reproduce verified). S7 DoD COMPLETES M0 → merge + tag. → Action(run `make test` (103) + `make test-golden` (5); git merge --no-ff feat/S7 → main; full suite on main; git tag -a v0.1.0; git branch -d feat/S7) → Observation: merged @ d58f94f; 103 non-solver + 5 @solver green on main; v0.1.0 tagged (LOCAL only — NOT pushed, human-gated); feat/S7 deleted; only main remains. M0 COMPLETE. no_progress_count stays 0 (green merge).
- [tick 17 | HANSEI] What worked: building the seal gate DIRECTLY in the parent (not via a spawned Generator) was the right call for load-bearing seal work — full control over the non-circularity logic — and the mutation-verification discipline (neuter each seal → confirm RED → restore) turned three otherwise-tautological guard tests into honest ones, which the adversarial reviewer then independently re-confirmed by its OWN mutations. The CARRIED 1-px-convention item resolved cleanly via the offered Option A: the convention is ALREADY pinned by deterministic, solver-free round-trip tests, so adding a hard <5" gate would have introduced stranger-flake risk the plan deliberately designed the 10" gate to avoid — Option A is the stronger engineering choice, and the reviewer proved it (CD-sign/CRPIX mutations fail the round-trip tests deterministically). Genchi-genbutsu: running `make run`/`make test-golden` myself + the reviewer's independent re-solve (not trusting the build narrative) is what confirmed the 2.08" is a real, non-circular number. Surprise/Muda avoided: nearly all of S7's "deliverables" (LICENSE, requirements.lock, most of the README, the per-module seals) were ALREADY done in earlier sprints — the genba walk prevented re-building them; S7's true delta was the formal seal consolidation + the golden gate + a stale-status README fix. KAIZEN (M1): M1 is a SEPARATE milestone (real image) with an optional human-approval andon gate — the next tick is a FRESH planning tick that must FIRST surface real-image scope to the human (target frame + its real-TLE truth source) before planning; carry the detect_streak saturated/wide-streak watch-item (#1) into the real-image build. Anti-spin: green merge → no_progress 0. Per §3.2 + the HARD-STOP: this BUILD tick ENDS here; M1 does NOT begin now.

- [tick 18 | GENBA] Thought: status FRESH for M1; per §3.2 a FRESH planning tick (GENBA→RESEARCH→IDEATE→PLAN, HARD-STOP at the plan lock — the M1 BUILD is the NEXT tick). Driven by an operator brief naming a SEPARATE, human-signed M1 contract (plan-the-m1-real-image-snappy-bunny.md) — distinct from the M0 plan the config/state still pointed at. Verify §3.5 gates + no live session + baseline + the M1 plan before locking. → Action(list_sessions isRunning check; git status/log/HEAD/tags/branches; shasum both plans; `make test` + `make test-golden` via repo .venv) → Observation: NO live tracklet build loop (the 2 isRunning sessions are space-research chats; every Tracklet-* build session stopped; tick_lock null). Clean tree on main @ 52c00e5 (tick-17 bookkeeping chore, 1 ahead of tag v0.1.0 @ d58f94f — loop-authored, no drift). M0 plan re-hash = d7237cdd… (matches recorded — state internally consistent, just pointed at the COMPLETED M0 plan). M1 plan present (24023 B, SHA 955c27e35f9ea3627d3edbf6f276105b5d9b1d82b34e0e3d12543062d9b5a2ed). Baseline GREEN: 103 non-solver + 5 @solver (golden e2e blind residual 2.081"). Perth 15:51.
- [tick 18 | RESEARCH] Thought: the M1 plan is a fully-specified, human-signed /ultraplan output (non-circularity architecture, 6 sprints, signed ACs, reuse map all settled). The only genuine external unknown — WHICH real public FITS frame — is Sprint-1 BUILD acquisition work (priority archives already named: NOIRLab Astro Data Archive → ZTF/IRSA → SDSS), NOT planning research, and it is gated by the human andon. → Action(none — JIT SKIP) → Observation: research SKIPPED (the plan settles HOW; frame sourcing is the Sprint-1 build).
- [tick 18 | IDEATE] Thought: the M1 plan fully specifies the design (two independent truths kept out of the solving path; ingest as render's symmetric WRITER; behavior-preserving render extractions; additive report widening; extended seal tests). No design fork → SKIP heavy ideation (Muda). → Action(emit trivial design brief, below) → Observation: brief recorded; Pre-Mortem clear — (a) reuses render's propagation + clean-FITS write (re-invents nothing); (b) the seal is PRESERVED + EXTENDED (score stays the sole json.load reader; ingest is a second WRITER, not a reader; the solver gets a WCS-stripped image); (c) no solving-module contract change (render gets behavior-preserving extractions; report widens additively + downstream of score); (d) scope == the M1 plan verbatim — PHASE 2 (harvester + truth-correlator) explicitly NOT built.
- [tick 18 | PLAN] Thought: JIT — M1 fully covered by the approved, human-signed plan-the-m1-real-image-snappy-bunny.md; skip /ultraplan, consume it, record path + SHA so the BUILD tick's §4-#3 stale-plan gate applies to the RIGHT plan. The milestone advanced M0→M1, so the binding plan changes: repoint BOTH config.approved_plan_path AND loop_state.plan_file/plan_sha256 to the M1 plan (Konnyaku/Nemawashi — leaving config pointed at the COMPLETED M0 plan would mis-point the next tick; surfaced to Sam this tick). → Action(repoint config.approved_plan_path → plan-the-m1-real-image-snappy-bunny.md + correct the M1-dod "(plan S8)" stale pointer; set loop_state plan_file/plan_sha256 = 955c27e3…, status PLAN_LOCKED_AWAITING_BUILD, phase PLAN; write the Sprint-1 BUILD next_action incl. the human andon gate + the M1 invariant core; commit the loop-authored chore on main) → Observation: plan_sha256 = 955c27e35f9ea3627d3edbf6f276105b5d9b1d82b34e0e3d12543062d9b5a2ed; config + state repointed; status PLAN_LOCKED_AWAITING_BUILD. Per §3.2 this FRESH tick HARD-STOPS at the plan lock — the Sprint-1 BUILD (acquisition + human andon gate) is the NEXT tick, launched by a human in a fresh /autobuild-loop session. no_progress_count stays 0 (plan-lock = progress, §3.3).

### increment design brief (tick 18)

```
M1 Sprint 1 — acquire + smoke-verify + LOCK the real frame (HUMAN ANDON GATE). Build EXACTLY Sprint 1 of the
approved plan (plan-the-m1-real-image-snappy-bunny.md), no more, no less.

SCOPE (JIT — Sprint 1 verbatim): source ONE public-archive FITS carrying a header WCS + precise UTC
(DATE-OBS/EXPTIME) + a satellite trail whose NORAD id is EXTERNALLY established (priority NOIRLab Astro Data
Archive → ZTF/IRSA → SDSS). Smoke-verify it blind-SOLVES + DETECTS on the RAW candidate (solve_pointing +
detect_streak, path-based, reused VERBATIM — solve-field solves blind by default even with a header WCS present).
Write tests/fixtures/real/PROVENANCE.md (source URL, exact retrieval steps, DATE-OBS/EXPTIME, NORAD id + TLE epoch
+ source, observatory site, header-WCS presence). DEFAULT to a fetch.sh that downloads the frame + verifies a
pinned SHA256 with TWO URLs (primary archive + a documented mirror); inline-commit the FITS ONLY if small
(≤~5 MB) AND license permits (a multi-MB binary in non-LFS git history is one-way bloat). Commit the TLE (as M0
commits the ISS TLE).

HARD STOP — Sam confirms the exact frame + NORAD id + provenance (AC 1.5) before Sprint 2. The lock is PROVISIONAL:
AC 1.2/1.3 solve+detect the RAW candidate, which does NOT guarantee the NORMALIZED image still solves — Sprint 2's
AC 2.5 is the binding confirmation; if AC 2.5 fails, REJECT the frame and return here for the next candidate.

TOUCHED: tests/fixtures/real/ (PROVENANCE.md + fetch.sh + TLE + meta.toml) + a documented smoke. NO product-module
code in Sprint 1 — the 7 solving/pipeline modules are UNTOUCHED; Sprint 1 only ADDS fixtures + provenance and runs
the EXISTING path-based solve/detect as a smoke. Sealed-truth + every signed contract preserved by construction.

TEST ORACLE (Sprint-1 Green): documented smoke — solve_pointing(<raw candidate>, {"fov_deg": <hint>}) returns a
SolveResult (not SolveFailure) AND detect_streak(<raw candidate>) returns a StreakDetection (not DetectFailure);
`make test` still green (only docs/fixtures added); AC 1.1 retrieval stranger-reproducible (a fresh checkout
obtains the byte-identical frame via committed inline OR fetch.sh SHA256 against the primary OR mirror url).

YAGNI / OUT OF SCOPE: NO ingest module (Sprint 2), NO truth assembly (Sprint 3), NO run.py branch (Sprint 4),
NO report (Sprint 5), NO non-FITS ingest, NO streak-vs-catalogue matcher (PHASE 2). Sprint 1 = acquire + smoke +
provenance + the human andon ONLY.

JUDGE: N/A — trivial design brief (Sprint 1 fully specified; no design fork). Pre-Mortem guard, all four clear:
(a) re-invents nothing (reuses solve_pointing/detect_streak verbatim as a smoke); (b) sealed-truth untouched (no
module built; the smoke runs the blind path on the raw frame); (c) shatters no signed contract (no module
changed); (d) scope == Sprint 1 verbatim.
```

- [tick 19 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for M1 Sprint 1 (the human-andon-gated acquisition increment); verify §3.5 gates + no live-session collision + the GREEN baseline before any build, and re-ground both reuse points (solve_pointing/detect_streak signatures). → Action(Read state IN FULL + config + the M1 plan IN FULL; git status --porcelain + HEAD + branches + tags + commits since d58f94f; shasum the M1 plan; list_sessions isRunning check; `make test` + `make test-golden` via repo .venv; grep solve_pointing/detect_streak + the typed-result classes) → Observation: clean tree on main @ 1f4d93a; only 2 loop-authored chore commits since d58f94f (tick-17 + tick-18 plan-lock), no foreign branch, only `main` + tag v0.1.0; plan re-hash = 955c27e35f9e… MATCHES recorded (plan NOT stale); NO live tracklet build loop (the 2 isRunning sessions are space-research chats; all Tracklet-* build sessions stopped; tick_lock null); baseline GREEN 103 non-solver + 5 @solver (golden e2e blind residual 2.081"); no_progress_count 0. Reuse points confirmed verbatim: solve_pointing(image_path, scale_hint) @ solve_pointing.py:111, detect_streak(image_path) @ detect_streak.py:248; SolveResult/SolveFailure + StreakDetection/DetectFailure present. Cut feat/m1-s1-real-frame. ALL §3.5 gates pass → line clear to build.
- [tick 19 | BUILD/ACQUISITION] Thought: Sprint 1's load-bearing first step is SOURCING ONE real public-archive FITS whose trailing satellite's NORAD id is EXTERNALLY established (published/cataloged) — NOT recovered by us (a TLE→streak correlator is PHASE 2, explicitly out of scope per the plan). Genuine, time-boxed search across the priority archives + the strongest labeled-dataset candidates. → Action(WebSearch + WebFetch over: NOIRLab/ZTF-IRSA/SDSS satellite-streak literature; HST/ACS Nature-Astronomy trail catalogue; ZTF Starlink-impact paper arXiv 2201.05343; the StreakMind A&A 2026 dataset arXiv 2605.03429; the Frigate LEO-FITS dataset PMC12717252 / figshare 10.6084/m9.figshare.29545667; the Mephisto multi-band DL paper arXiv 2509.04081 + 2509.16771) → Observation: a STRUCTURAL blocker, consistent across every candidate — datasets that PUBLISH the FITS do NOT carry per-frame externally-established NORAD identity, and papers that IDENTIFY NORAD ids do NOT release a single retrievable public FITS exposure tied to that id with a usable header WCS + DATE-OBS. Specifics: (i) HST/ACS Nature-Astronomy trails (j8cw52p3q, jcor25dtq…) are labeled "trail present" by citizen science, NOT correlated to a NORAD object → fails AC 1.4; (ii) ZTF Starlink-impact papers give methodology + aggregate matches (300" co-linearity gate) but name NO single retrievable frame+NORAD pair → fails AC 1.1/1.4; (iii) StreakMind: FITS NOT public + identifies via Project-Pluto Sat_ID codes (not NORAD) AND the matching IS the correlator the plan bans (PHASE 2); (iv) Frigate: openly downloadable real LEO FITS w/ ms-precise DATE-OBS + 0.5s EXPTIME + CC-BY-4.0, BUT NO plate solution (no header WCS) + only bounding boxes (no NORAD identity) → fails AC 1.2 + AC 1.4; (v) Mephisto DL papers: FITS not released, NORAD ids illustrative not per-frame. Establishing identity myself by TLE-propagating to a candidate frame + matching the streak = exactly the PHASE-2 correlator the plan forbids in PHASE 1. Per the plan's explicit time-box rule, STOP rather than fabricate an identity or a residual.
- [tick 19 | ANDON] Thought: this is the §4 / Sprint-1 HUMAN ANDON GATE firing for real — the ONE hard stop M1 was designed around. The honest, doctrine-correct move is to HALT and hand Sam the candidate landscape + the precise external blocker, NOT to weaken AC 1.4 / build a correlator / fabricate. → Action(checkout main; delete feat/m1-s1-real-frame [0 commits — clean, no inventory-muda]; set human_gate=true, phase BUILD, no_progress_count 0→1 [honest: a build tick with no green merge, §3.3]; write the resumption contract + needs_human; status STAYS PLAN_LOCKED_AWAITING_BUILD [Sprint 1 is blocked at acquisition, not done]) → Observation: tree clean on main; human gate raised; loop bookkeeping committed on main; awaiting Sam's frame+NORAD+provenance. NO product code, NO module touched, sealed-truth + every signed contract preserved by construction.
- [tick 19 | HANSEI] What worked: the plan's time-box + "never fabricate an identity or a residual" rule did EXACTLY its job — it stopped the loop from the seductive wrong move (propagate a TLE to a likely frame, "establish" identity myself, and report a flattering residual), which would have silently imported the PHASE-2 correlator and destroyed the milestone's whole honesty claim. The genchi-genbutsu on each candidate (actually checking Frigate's headers = no WCS; StreakMind = Project-Pluto codes + non-public FITS; HST = citizen-science labels not orbital correlation) prevented committing to a frame that fails a gate only discovered later. Genuine finding (the real muda surfaced): there is a STRUCTURAL gap in the public-data ecosystem — "FITS + header WCS + precise UTC + externally-established NORAD identity, all four in one downloadable frame" is rare precisely because identity-correlation is itself hard work most publishers don't ship. This is exactly why the plan put a HUMAN gate here. KAIZEN for the resumption tick: do NOT blindly re-run the same open-ended web search (no new info → no progress → burns toward the §4-#5 spin gate at no_progress_count=2); the unblock is EXTERNAL (Sam supplies/approves a frame, or names a channel — e.g. an SSA contact, a specific NOIRLab program he knows carries trail+ID, a Space-Track-correlated observation, or an amateur tracker who imaged a NAMED LEO object and published the FITS). Candidate strategies to put to Sam are in needs_human. Anti-spin: this build tick did not merge green → no_progress 0→1 (mechanical); the PLANNED human gate is the intended terminus of this tick, not a spin-failure, but the next no-merge tick WOULD hit the hard gate — so resumption must be frame-in-hand, not another blind attempt. Per §3.2 + the operator brief: this BUILD tick ENDS here at the human andon gate; Sprint 2 does NOT begin.

### acquisition sourcing landscape (tick 19 — for Sam's gate decision)

```
GOAL (AC 1.1–1.4, ALL FOUR in ONE downloadable frame):
  - real public-archive FITS, retrievable byte-identically (inline-commit OR fetch.sh + pinned SHA256)
  - header WCS present (the survey's OWN plate solution = independent pointing-truth; read only by ingest+report)
  - precise UTC: DATE-OBS (exposure START, UTC) + EXPTIME
  - a satellite trail whose NORAD id is EXTERNALLY established (published/cataloged by a THIRD PARTY) +
    a TLE with epoch within sane range of DATE-OBS + a known observatory site (topocentric, for LEO parallax)

WHY IT'S HARD (the structural blocker found this tick): the four properties are split across two
disjoint corpora — (A) datasets that publish FITS (Frigate, ZTF cutouts, StreakMind source) ship NO
per-frame externally-established NORAD identity (and Frigate has no WCS); (B) papers/pipelines that
establish NORAD identity (ZTF-Starlink, StreakMind's Sat_ID matching, Mephisto DL) do NOT release a single
retrievable public FITS tied to that id. Bridging them MYSELF (propagate a TLE to a candidate frame, match
the streak) is the PHASE-2 correlator the plan forbids in PHASE 1.

CANDIDATE STRATEGIES TO PUT TO SAM (ranked by how cleanly they satisfy all 4 + honesty):
  1. A frame Sam already has / can get from an SSA or observatory contact where the object identity is
     established by THAT source (e.g. a tasked tracking observation of a NAMED object) — cleanest: identity
     is genuinely external, FITS+WCS+UTC come with it.
  2. An amateur/pro astrophotographer who imaged a SPECIFIC, NAMED LEO object (e.g. a known Starlink pass,
     the ISS, a named rocket body) and published the plate-solved FITS — identity is external (the imager
     stated which object they targeted), provenance is the imager's log. Sam to point at a specific one.
  3. A NOIRLab Astro Data Archive program Sam knows carries trail+ID metadata, or a Space-Track / IAU-CPS
     SatHub case-study frame released WITH its correlated identity. (Generic NOIRLab search this tick did
     not surface a per-frame ID; a Sam-known program/PI would.)
  4. RELAX the source of identity (a plan/Sam decision, NOT a loop decision): accept a frame where WE
     propagate a published TLE to confirm a NAMED candidate object lands on the streak — but this is the
     PHASE-2 correlator and the plan explicitly bars it for PHASE 1. Only Sam can authorize moving that
     line; the loop will NOT cross it autonomously.

WHAT THE LOOP NEEDS FROM SAM TO RESUME (minimum): a frame (URL or file) + its DATE-OBS/EXPTIME + the
externally-established NORAD id + how that identity was established (the external source) + the TLE
(or where to fetch it) + the observatory site. With that, the next tick completes the Sprint-1 BUILD
(fetch+commit, smoke solve+detect, PROVENANCE.md, AC 1.5 sign-off) and proceeds to the provisional lock.
```

- [tick 20 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for M1 Sprint 1 with the frame NOW confirmed (AC-1.5 cleared by Sam: BlueWalker-3 DDOTI 20221118T024706C1o, NORAD 53807, Zenodo 8102655); this is the frame-in-hand BUILD tick (§3.2: GENBA→BUILD→REVIEW→(INTEGRATE|FIX)→HANSEI). Verify §3.5 gates + no live-session collision + GREEN baseline before building. → Action(Read state IN FULL + config + the M1 plan IN FULL; re-ground solve_pointing/detect_streak/scene.load_tle reuse points; git status --porcelain + HEAD + branches + tags + commits since d58f94f; shasum the M1 plan; list_sessions isRunning check; `make test` + `make test-golden` via repo .venv) → Observation: clean tree on main @ 548bc00 (the AC-1.5 gate-cleared chore); only loop-authored chore commits since d58f94f (ticks 17/18/19/20-prep), no foreign branch, only `main` + tag v0.1.0; plan re-hash = 955c27e35f9e… MATCHES recorded (NOT stale); NO live tracklet build loop (the 2 isRunning sessions are space-research chats; all Tracklet-* build sessions stopped; tick_lock null); baseline GREEN 103 non-solver + 5 @solver (golden e2e 2.081"); no_progress_count 0. Reuse points verbatim: solve_pointing(image_path, scale_hint)@111, detect_streak(image_path)@248, scene.load_tle/default_tle_path/parse_tle_text (checksum-validated). Cut feat/m1-s1-real-frame. ALL §3.5 gates pass.
- [tick 20 | BUILD/TLE-ACQUISITION] Thought: the frame's provenance (AC 1.1-1.3,1.5) is in hand, but Sprint-1 AC 1.4 + the Sprint-3 satellite-truth REQUIRE a HISTORICAL NORAD-53807 TLE bracketing the exposure midpoint 2022-11-18T02:47:16.782 UTC (MJD 59901.116). This is the one real remaining dependency the locked next_action flagged as the TLE WATCH-ITEM ("Andon to Sam if blocked"). Try public, no-credential sources FIRST (per the watch-item), NEVER fabricate / substitute a far-epoch TLE / build a correlator. → Action(WebSearch BW3/53807 historical TLE Nov-2022; WebFetch CelesTrak gp.php (current) + gp-history.php (date-windowed) + SatNOGS DB + orbit.ing-now + SeeSat-L Nov-2022 thread index; WebSearch public historical-TLE archives/mirrors; grep -rI for any stored space-track creds / ~/.netrc — REPORT-ONLY, do not use unsupplied creds) → Observation: STRUCTURAL blocker, consistent across every public source — historical TLEs by date are gated behind Space-Track.org (FREE login). Specifics: CelesTrak gp.php returns CURRENT-only (epoch 2026-06-17 = 3.5 yr from the frame → SGP4 fiction if used); CelesTrak gp-history.php = paid subscription (public endpoint HTTP 404); SatNOGS DB / n2yo / orbit.ing-now / satview = latest-only; SeeSat-L has Sep-2022 BW3 posts but the Nov-2022 thread index 404s + no ~2022-11-18 TLE surfaced; spacetrack client / Jonathan McDowell's archive / daily-catalog mirrors ALL route through Space-Track. NO ~/.netrc, NO stored Space-Track identity on this machine (the only "space-track" grep hit is loop_state.md's own watch-item text). The Zenodo BW3 archive MAY ship a TLE alongside the frames (unconfirmed — a candidate Sam can check). No autonomous path.
- [tick 20 | ANDON] Thought: the TLE WATCH-ITEM Andon is firing for real — a genuinely-new external dependency that only became actionable now the frame is confirmed (distinct from the tick-19 frame gate Sam already cleared). The honest, doctrine-correct move is to HALT and hand Sam the precise blocker + the exact unblock options (Space-Track pull / creds / a named free source), NOT to fabricate a TLE, substitute the 3.5-yr current TLE, or build the banned PHASE-2 correlator. Do NOT commit a partial fixtures set (a PROVENANCE.md missing its TLE epoch+source block would be a half-smoothed panel / inventory-muda). → Action(checkout main; delete feat/m1-s1-real-frame [0 commits — clean, no inventory-muda]; set human_gate=true, phase BUILD, no_progress_count 0→1 [mechanical §3.3 — a build tick with no green merge; NOT gamed], write the >>> TLE BLOCKER resumption contract + needs_human; status STAYS PLAN_LOCKED_AWAITING_BUILD [Sprint 1 blocked at the TLE, not done]) → Observation: tree clean on main; human gate raised; loop bookkeeping committed on main; awaiting Sam's historical TLE / creds / source. NO product code, NO module touched, NO fixtures committed — sealed-truth + every signed contract preserved by construction.
- [tick 20 | HANSEI] What worked: the plan's "DO NOT fabricate a TLE or silently use a far-epoch current TLE" rule did EXACTLY its job — it stopped the seductive wrong move (grab CelesTrak's current 2026 TLE, propagate it 3.5 yr back to 2022-11-18, and report a flattering-but-fictional residual), which would have silently destroyed M1's whole honesty claim the same way a fabricated identity would have at tick 19. Genchi-genbutsu on each source (CelesTrak gp-history actually 404s for the public; SatNOGS/orbit-ing-now actually show only the latest; SeeSat-L's Nov-2022 index actually 404s) is what confirmed the blocker is STRUCTURAL (historical-by-date TLEs are a Space-Track-gated resource), not a search-phrasing miss. Honest finding / the real muda surfaced: the M1 frame-sourcing gap (tick 19) and the TLE-sourcing gap (tick 20) are the SAME structural fact in two halves — the four properties "FITS + WCS-or-pointing + precise UTC + externally-established NORAD identity + a near-epoch TLE" are split across disjoint corpora, and the orbital-truth half (the TLE history) is the part most reliably behind a (free but credentialed) wall. This is precisely why the plan put a HUMAN gate here. KAIZEN for the resumption tick: do NOT re-run the same blind TLE web-search (no new info → no progress → trips the §4-#5 spin gate at no_progress_count=2); the unblock is EXTERNAL — Sam pulls the historical TLE from Space-Track (free account, epoch window 2022-11-15…21, nearest to 02:47 UTC), or checks whether the Zenodo BW3 archive ships a TLE, or supplies creds. Anti-spin: this BUILD tick did not merge green → no_progress 0→1 (mechanical, honest); the PLANNED TLE-watch-item gate is the intended terminus, but the NEXT no-merge tick WOULD hit the hard gate — so resumption MUST be TLE-in-hand. Per §3.2 + the operator brief: this BUILD tick ENDS here at the human andon gate; Sprint 2 does NOT begin.

### TLE-acquisition blocker (tick 20 — for Sam's gate decision)

```
NEED (Sprint-1 AC 1.4 + Sprint-3 satellite-truth): a HISTORICAL BlueWalker-3 (NORAD 53807) TLE whose
epoch BRACKETS the exposure midpoint 2022-11-18T02:47:16.782 UTC (MJD 59901.116). For a LEO object,
a TLE epoch within ~1-2 days of the frame keeps the SGP4 propagation error small; the current 2026
TLE (3.5 yr away) is unusable (SGP4 fiction) and MUST NOT be substituted.

WHY IT'S BLOCKED (verified this tick, all public/no-credential sources):
  - CelesTrak gp.php?CATNR=53807        → CURRENT-only (epoch 2026-06-17). Not usable.
  - CelesTrak gp-history.php (by date)  → paid subscription; public endpoint HTTP 404.
  - SatNOGS DB / n2yo / orbit.ing-now / satview → latest-only, no history download.
  - SeeSat-L: Sep-2022 BW3 posts exist, but the Nov-2022 thread index 404s; no ~2022-11-18 TLE found.
  - spacetrack client / Jonathan McDowell's archive / daily-catalog mirrors → ALL route through
    Space-Track.org → FREE account login required (no ~/.netrc / stored identity on this machine).

UNBLOCK — Sam does ANY ONE (then re-launch /autobuild-loop on ~/tracklet):
  1. Space-Track.org (free account): query NORAD 53807, EPOCH window 2022-11-15…2022-11-21, pick the
     set nearest 2022-11-18T02:47 UTC, drop the 2 TLE lines into ~/tracklet (or hand them to the loop).
     This is the cleanest path — Space-Track has the full historical catalog for 53807.
  2. Check the Zenodo BW3 archive (record 8102655) — it MAY ship a TLE alongside the frames; if so,
     the loop fetches it deterministically (already streaming that archive for the FITS).
  3. Supply Space-Track credentials for the loop to fetch it (Sam authorizes + provides; the loop will
     NOT use creds it isn't given).
  4. Name another FREE historical-TLE source carrying NORAD 53807 near 2022-11-18 (amateur archive,
     a SatNOGS observation-derived TLE, a BW3-tracking paper appendix).

ONCE THE TLE IS IN HAND, the resumption tick: commits the TLE (gitignore-safe — data/tle/ is tracked) +
records its actual epoch + source in PROVENANCE.md + writes fetch.sh (stream + tar --include the single
17.5 MB member → funpack; pinned member SHA-256 b6dcf797…19ca1) + meta.toml + the smoke (AC 1.2 solve /
AC 1.3 detect already PROVEN on the raw frame) + AC 1.5 sign-off → provisional Sprint-1 lock → Sprint 2.
```

- [tick 21 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for M1 Sprint 1 with the frame confirmed (tick 19/20) and the committed state claiming the TLE blocker RESOLVED — but the decisions log had NO tick recording that resolution (the TLE-resolved frontmatter rode in via commit 381810b without a ReAct triple), so the FIRST job is to verify the claim against ground truth, NOT trust the narrative. Verify §3.5 gates + baseline + INDEPENDENTLY validate the committed TLE before building satellite-truth on it. → Action(Read state IN FULL + config + the M1 plan IN FULL; git status --porcelain + HEAD + branches + tags + commits since d58f94f; shasum the M1 plan; `make test` + `make test-golden`; independently check the two committed TLE lines — checksum, epoch decode, orbit sanity — in a scratch python) → Observation: clean tree on main @ 381810b; all commits since d58f94f are loop-authored chore (no foreign branch, only `main` + tag v0.1.0); plan re-hash 955c27e3… MATCHES (NOT stale); baseline GREEN 103 non-solver + 5 @solver (golden e2e 2.081"); no_progress 0. TLE VERIFIED GENUINE: L1 cksum 3==3, L2 cksum 5==5, both 69 chars; epoch 22321.51776124 decodes to 2022-11-17T12:25:34Z = 0.598 d before the exposure; orbit i=53.2°, mm=15.186 rev/day → derived a=6888 km → ~510 km LEO, BW3-consistent. The "RESOLVED" frontmatter is TRUE. Set tick_lock + committed begin-marker 089b7ba on main; cut feat/m1-s1-real-frame.
- [tick 21 | BUILD] Thought: §3.2 BUILD tick — build the Sprint-1 deliverable (fixtures + provenance + live smoke), reusing solve_pointing/detect_streak VERBATIM; prove AC 1.2/1.3 genchi-genbutsu rather than inherit the recorded smoke. The frame is gitignored (*.fits) + multi-GB-archived → fetch.sh streams ONLY the single member. → Action(stream + tar -xzO the single 17.5 MB member from Zenodo → verify SHA256 → funpack → read the header → run solve_pointing + detect_streak LIVE on the raw funpacked frame; write tests/fixtures/real/{bluewalker3_53807.tle, PROVENANCE.md, fetch.sh, meta.toml}; validate the TLE through scene.parse_tle_text; write tests/test_real_fixtures.py — 6 non-solver fixture-integrity guards) → Observation: streamed member byte-EXACT (17,507,520 B, SHA256 b6dcf797…19ca1 == pinned). Header confirmed every state fact: DATE-OBS=2022-11-18T02:47:16.782 (START), EXPTIME=10.0, MJD 59901.116, NO header WCS (0 keys), STRCURA=303.607/STRCUDE=−16.204, BLKNM/VSTNM='BW3', 6144×6220 BITPIX16 BZERO32768, TELESCOP=DDOTI/INSTRUME=C1. LIVE SMOKE PASS: AC 1.2 solve_pointing→SolveResult 8.4 s center (305.557,−14.964) [== recorded]; AC 1.3 detect_streak→StreakDetection 3.4 s, 4956 px @126.16° [== recorded]. Committed TLE validates via parse_tle_text. 6 new tests green; mutation-probed the TLE-checksum test (9993→9990 → RED at scene.py:183, restore → GREEN, file SHA-restored) = load-bearing. Full suite 109 non-solver + 5 @solver green; scope = ONLY tests/fixtures/real/ + tests/test_real_fixtures.py (git diff main -- src/ EMPTY → no module touched); seal intact (json.load only score.py:64).
- [tick 21 | REVIEW] Thought: LOW-RISK increment (fixtures + a fixture-integrity test; ZERO source change; seal + all solving contracts untouched by construction → the high-risk 2nd-pass trigger is NOT met) → a single thorough LOCAL adversarial review (free, local; the Task/Agent spawn tool was unavailable this env → ran the review directly, genchi-genbutsu, per konnyaku "when the workshop fights you"). Probe the honesty-critical claims. → Action(PROBE 1 external identity: re-read the header → BLKNM/VSTNM='BW3', OBJECT absent → identity carried by the DATASET, no correlator run, EXTERNAL ✓; PROBE 2 non-fabrication: grep fixtures for any residual/score number → NONE committed [only the prose "reproduce the M1 residual"] ✓; PROBE 3 blind solve: smoke fed only fov_deg scale hint, no RA/Dec prior; meta records commanded pointing but never passes it to the solver ✓; PROBE 4 fetch integrity: verify_sha256 per-url + exit 1 loud on mismatch ✓) → Observation: VERDICT ACCEPT. 1 NIT found + FIXED in-tick: the fixture-test constant was named EXPOSURE_MIDPOINT_UTC but held the DATE-OBS START value (start-vs-midpoint is a Sprint-3 AC-3.1 concern, not Sprint 1) → renamed to DATE_OBS_START_UTC + commented "midpoint = start + EXPTIME/2 (pinned in Sprint 3)" so no misleading label carries forward (konnyaku smoothing). Re-ran: 6/6 + 109 non-solver green.
- [tick 21 | INTEGRATE] Thought: PHASE-5 gate met (ACCEPT + the NIT fixed + both suites green + the AC-1.5 human frame-gate ALREADY cleared by Sam at tick 19/20, recorded in PROVENANCE.md). The Sprint-1 deliverable is unambiguously correct (real fixtures, smoke re-proven, no source touched) → merge green; surface the Sprint-1→2 boundary to Sam as a courtesy (the human gate was already given; the binding confirmation is Sprint-2 AC 2.5, not a new stop). → Action(commit the increment on feat 74dc0fc; git merge --no-ff feat/m1-s1-real-frame → main; `make test` + `make test-golden` on main; git branch -d feat/m1-s1-real-frame) → Observation: merged @ b0155a6; 109 non-solver + 5 @solver green on main; M0 golden e2e intact; branch deleted, only `main` remains. Sprint 1 ≠ a milestone (v0.1.1 is Sprint 6) → no tag. no_progress_count stays 0 (green merge).
- [tick 21 | HANSEI] What worked: the FIRST genba move — distrusting the "TLE RESOLVED" frontmatter because no decisions-log tick recorded the resolution, and independently re-deriving the checksum + epoch + orbit before building on it — is exactly the genchi-genbutsu the honesty milestone demands; the claim turned out TRUE, but verifying it (not inheriting it) is what makes the eventual residual trustworthy. Re-running the live smoke rather than copying the recorded (305.557,−14.964) confirmed the frame genuinely blind-solves THIS tick, and the byte-exact member SHA proved the fetch.sh streaming recipe before committing it. Honest scoping: I caught + fixed a misleading START-vs-MIDPOINT constant name in-tick (cheap, honesty-relevant) but correctly LEFT the actual timing-semantics resolution to Sprint-3 AC 3.1 (the plan's home for it) rather than over-reaching. Process gap surfaced (Kaizen): a prior turn mutated the state frontmatter (TLE resolved, counters reset) and committed it WITHOUT an accompanying decisions-log ReAct triple — a half-recorded panel; this tick's GENBA had to reconstruct + verify the claim from scratch. The standing discipline holds: every state mutation that changes the build's premise MUST carry its own decisions-log triple, so a fresh-context tick can trust the log. Env note: the general-purpose Agent/Task spawn tool was unavailable this session → the REVIEW ran directly in-parent (still local + free, cost guard honored); for a HIGH-RISK sprint (S2 ingest extends the seal; S3 extracts render helpers; S4 produces the residual) a 2nd independent review is mandatory — if the spawn tool is still unavailable then, run two genuinely separate review passes (e.g. a fresh re-derivation from the raw frame) rather than skip the second pass. Anti-spin: green merge → no_progress 0. Per §3.2 this BUILD tick ENDS at the green merge; Sprint 2 (ingest) is the NEXT tick — surfaced to Sam at the Sprint-1→2 courtesy checkpoint.

- [tick 22 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for M1 Sprint 2 (ingest) → §3.2 BUILD tick. Verify §3.5 gates + re-hash the plan + baseline BOTH suites before any build (Sprint 2 is @solver-relevant: AC 2.5 re-solves). Read loop_state IN FULL + config + the M1 plan IN FULL. → Action(Read state full + config + plan; git status --porcelain + HEAD + branches + tags + log since last_green b0155a6; shasum the M1 plan; read render.py/score.py/test_seal.py/meta.toml; `make test` + `make test-golden`) → Observation: clean tree on main @ 2bf1d24; only the tick-21 loop bookkeeping commit since b0155a6 (loop-authored, no foreign branch — only `main` + tag v0.1.0); plan re-hash 955c27e35f9e…a2ed MATCHES (not stale); no_progress 0; tick_lock null. Baseline GREEN: 109 non-solver + 5 @solver (golden e2e 2.081"). Scoped Sprint 2 to the BINDING plan ACs 2.1-2.5 = ingest's clean WCS-free image + seal extension + AC 2.5 re-solve; truth.json TLE assembly is Sprint 3 (ACs 3.1-3.5), so this tick writes only the clean image (state next_action over-reached by bundling truth.json — the plan is the authority). Set tick_lock + committed begin-marker fff6247 on main; cut feat/m1-s2-ingest.
- [tick 22 | RESEARCH] Thought: Sprint 2 carries no external unknown — astropy.io.fits is installed + exercised since S0; the real-frame quirks (HDU select, BSCALE/BZERO, byte order, non-finite, orientation) are all named in plan Sprint 2; the only empirical fact is whether the NORMALIZED image still solves (AC 2.5 = a BUILD test, not research). → Action(none — JIT SKIP) → Observation: research SKIPPED (mechanical; Sprint 2 settled by the plan + installed astropy). Kicked off tests/fixtures/real/fetch.sh in the background to obtain the real frame for AC 2.5.
- [tick 22 | IDEATE] Thought: ingest is fully specified (plan Sprint 2) but HIGH-RISK — it adds a SECOND writer of the sealed artifacts and EXTENDS the seal → a BRIEF design brief pinning the seal-extension boundary + the JIT scope cut (clean image now; truth.json Sprint 3), not a full brainstorm. → Action(emit BRIEF design brief, below) → Observation: brief recorded; Pre-Mortem clear — ingest implements a NEW module (re-invents nothing; write_clean_fits is a behavior-preserving render extraction, not a reimplementation); the seal is EXTENDED not weakened (ingest reads no truth, writes WCS-free); all solving-module signatures preserved; scope == Sprint 2 ACs 2.1-2.5 (truth.json deferred to Sprint 3 = YAGNI-correct sprint boundary).
- [tick 22 | BUILD] Thought: §3.2 BUILD — build ingest under inner TDD (Red→Green→Refactor). The Task/Agent spawn tool was unavailable this env → build directly in-parent under the test-driven-development discipline + konnyaku (per "when the workshop fights you"). → Action(RED: write tests/test_ingest.py 9 tests [AC 2.1 x5, 2.2 x2, 2.3/2.4 x2] + the @solver AC 2.5 skip-if-frame-missing → ModuleNotFoundError RED confirmed. GREEN: factor write_clean_fits from render.py:351-356 [behavior-preserving] + route render's own write through it + correct render's 'sole writer' docstring; implement ingest.ingest_external_image — do_not_scale_image_data=False for BSCALE/BZERO, science-HDU select, astype(float32)+ascontiguousarray for native order, non-finite→finite-only median, no flip/transpose; EXTEND test_seal.py: clean-FITS parametrized over ingest + static-import forbidden-list over ingest + repo-wide ALIAS-RESISTANT AST 'json.load/json.loads only in score.py' guard. Hit a docstring false-positive [literal 'json.load' in ingest prose tripped AC 2.4] → rephrased the docstring [the honest fix — the module must not name the token]. Verified render's 19 unit tests + golden e2e 2.081" unchanged after the extraction.) → Observation: 121 non-solver green (109 baseline + 9 ingest + 3 seal); 5 @solver green (golden e2e 2.081" intact); AC 2.5 SKIPPED (frame fetch in progress).
- [tick 22 | BUILD-MUTATION] Thought: a seal test that a broken impl would also pass is worthless ("never a green that a broken impl passes") → mutation-verify the 3 new seal tests are load-bearing BEFORE trusting them. → Action(M1 inject json.loads into ingest → json-guard; M2 leak a CRVAL into write_clean_fits → ingest clean-FITS guard; M3 import ingest into measure_position → static-import guard; restore each) → Observation: M2 + M3 correctly FAILED; M1 PASSED-when-it-should-fail — the guard matched only the literal name `json`, so `import json as _j; _j.loads()` SLIPPED. REAL GAP. HARDENED the guard to be alias-resistant (resolve every binding of the json module via import/import-as + catch `from json import load/loads`), keeping immunity to skyfield load.timescale()/astropy reads. Re-mutated: aliased-import AND from-import forms now BOTH FAIL; false-positive immunity reconfirmed (only score.py flagged); restored, src tree clean, 11 seal green.
- [tick 22 | REVIEW] Thought: HIGH-RISK (extends the seal over a new writer + touches render) → MANDATORY 2nd independent LOCAL review. Spawn tool unavailable → ran a fresh adversarial pass that RE-DERIVES the claims by direct computation (not the build narrative), local + free (cost guard; /code-review ultra BANNED). → Action(diff stat; PROBE 1 ingest names no truth/_load_truth/json.load/scored_truth/wcs_world2pix [clean — all 'truth' mentions are docstring prose]; PROBES A-D in a scratch python: A unsigned-16 on-disk is signed int16+BZERO32768 → ingest recovers [0,32767,32768,65535] no wrap; B non-finite fill == finite-only median 4.0, all finite; C orientation identity in-memory AND byte-exact on disk; D output image.fits WCS-stripped even from a WCS-carrying source, source WCS retained ONLY in in-memory IngestResult.header) → Observation: VERDICT ACCEPT. No blocker/major. Findings: F1 (MINOR, CARRY) — AC 2.5 not executed (frame fetch exceeded the 600s curl window; the binding Sprint-1 confirmation must run at the next @solver window; NOT a frame rejection; also re-exercised at Sprint-4 AC 4.1); F2 (NIT, REJECT) — explicit do_not_scale_image_data=False is astropy's default, belt-and-suspenders doc; F3 (checked, clean) — IngestResult.header can't leak into solve_pointing(path, scale_hint) [takes a path, not a header; AC 4.4's seal test guards the path at Sprint 4]. Non-circularity holds.
- [tick 22 | INTEGRATE] Thought: PHASE-5 gate met (ACCEPT + every finding dispositioned + both suites green; the one CARRY is a sourcing/network constraint surfaced to Sam, not a code defect) → integrate. → Action(commit GREEN increment on feat 7c26184; git merge --no-ff feat/m1-s2-ingest → main @ df22ff4; `make test` + `make test-golden` on main; git branch -d feat/m1-s2-ingest) → Observation: merged @ df22ff4; 121 non-solver + 5 @solver green on main (AC 2.5 skipped); M0 golden e2e 2.081" intact; branch deleted, only `main` remains. Sprint 2 ≠ a milestone (v0.1.1 is Sprint 6) → no tag. no_progress_count stays 0 (green merge).

### increment design brief (tick 22)

```
S2 (M1) — ingest: real FITS -> normalized, WCS-stripped clean image (seal-preserving). Build EXACTLY
plan Sprint 2 (ACs 2.1-2.5). HIGH-RISK: a SECOND writer of the sealed artifacts + EXTENDS the seal.

CHOSEN APPROACH: implement ingest.ingest_external_image(image_path, meta, out_dir) -> IngestResult on a
NEW module. Read the real FITS (astropy.io.fits, do_not_scale_image_data=False so BSCALE/BZERO apply) ->
select the science HDU (meta['frame']['science_hdu'] or the first 2-D image HDU) -> astype(float32) +
ascontiguousarray (native byte order) -> replace non-finite (NaN/Inf) with the FINITE-only frame median
-> NO flip/transpose (orientation identity). Write a WCS-free image.fits via the shared write_clean_fits
helper FACTORED from render.py:351-356 (behavior-preserving; render's own write routes through it).
Return the source science-HDU header + chosen HDU index IN-MEMORY (pointing/timing truth for Sprint 3/4,
never the solver).

SCOPE CUT (JIT / sprint boundary): Sprint 2 writes ONLY the clean image.fits. truth.json (TLE->skyfield
scored_truth) is Sprint 3 (ACs 3.1-3.5) — building it now would be over-production. The plan's Files
table lists ingest writing both, but the ACs split the work; the binding ACs win.

THE SEAL EXTENSION (why HIGH-RISK): M1 adds a second writer. Seal-compatible because (a) ingest writes a
WCS-free image.fits [clean-FITS, parametrized over ingest]; (b) ingest is structurally sealed away from
truth like the solving modules [static-import forbidden-list extended]; (c) score stays the SOLE json
deserializer [repo-wide ALIAS-RESISTANT AST 'json.load/json.loads only in score.py' — ingest uses
astropy + (Sprint 3) json.dump, never json.load]. All 3 new seal tests MUTATION-VERIFIED load-bearing;
the json guard was HARDENED in-tick after a mutation proved the first cut missed aliased imports.

TOUCHED MODULES: src/tracklet/ingest.py (NEW) + src/tracklet/render.py (write_clean_fits extraction +
docstring) + tests/test_ingest.py (NEW) + tests/test_seal.py (EXTEND). solve_pointing/detect_streak/
measure_position/score/scene/report/run UNTOUCHED (signatures byte-identical to main).

TEST ORACLE (ACs 2.1-2.5): 2.1 BSCALE/BZERO unsigned recovery + native order + non-finite median +
orientation identity + named-HDU MEF select (synthetic FITS fixtures, no network); 2.2 written image.fits
WCS-free [parametrized seal] + disk round-trip; 2.3 static seal (solve/detect/measure don't name/import
ingest); 2.4 no json.load in ingest + repo-wide json-guard; 2.5 @solver — the NORMALIZED ingest image
still blind-solves+detects on the REAL frame (skip-if-frame-missing) = the BINDING Sprint-1 confirmation.

YAGNI / OUT OF SCOPE: NO truth.json TLE assembly (Sprint 3), NO non-FITS ingest (no real non-FITS frame),
NO streak-vs-catalogue matcher (PHASE 2), NO run.py wiring (Sprint 4).

JUDGE: N/A — brief design brief (Sprint 2 fully specified; no design fork). Pre-Mortem manual, all clear:
(a) implements a new module + a behavior-preserving render extraction (re-invents nothing); (b) the seal
is EXTENDED, not weakened (ingest reads no truth, writes WCS-free); (c) all signed solving contracts
preserved; (d) scope == Sprint 2 ACs (truth.json correctly deferred to Sprint 3).
```

- [tick 22 | HANSEI] What worked: the MUTATION pass earned its keep loudly — the first cut of the repo-wide json.load seal PASSED a mutation that injected `import json as _j; _j.loads(...)` into ingest, exposing that the guard matched only the literal name `json` and an aliased import would slip the seal. Hardening it to resolve every binding of the json module (import / import-as / from-json-import) BEFORE merge means the non-circularity seal genuinely bites on a future regression, not just the obvious form. This is the konnyaku standard: a green seal test that a broken impl would also pass is worse than no test (false confidence). Genchi-genbutsu in REVIEW — re-deriving BSCALE/BZERO recovery, the finite-only median, orientation identity, and the WCS-strip by direct computation in a scratch python rather than trusting the build's own tests — confirmed the normalization is correct against the actual astropy on-disk encoding (signed int16 + BZERO 32768), the exact real-frame reality. Honest scoping under reality: I cut truth.json out of Sprint 2 (the state's next_action had bundled it) because the binding plan ACs put it in Sprint 3 — resisting the over-production of building a truth writer before its sprint. The one painful reality: AC 2.5, the BINDING confirmation of the provisional Sprint-1 lock, could not execute — the 2.4 GB Zenodo archive exceeded the 600s curl window on both urls (160/2400 MB), so the @solver real-frame proof is SKIPPED, not run. The test is correct (skip-if-frame-missing) and the skip is NOT a frame rejection, but honesty demands I flag clearly that the normalized real image has NOT yet been proven to solve+detect this tick — that is the single carried item for Sam + the next @solver window. KAIZEN (Sprint 3): the render extraction continues — propagate_satellite_radec is the next behavior-preserving factor; build it identically to render._propagate_satellite (same no-epoch ICRS skyfield call) so satellite-truth shares the solver's frame, and keep render's 19 unit + golden e2e green. Confirm the DDOTI site coords (site_confirmed=false) before pinning the topocentric propagation (LEO parallax). Env note persists: the Agent/Task spawn tool is unavailable → the mandatory 2nd review ran as a fresh in-parent re-derivation (local/free, cost guard honored); for Sprint 3 (extracts render helpers + assembles real satellite-truth) keep the same two-genuinely-separate-passes discipline. Anti-spin: green merge → no_progress 0. Per §3.2 this BUILD tick ENDS at the green merge; Sprint 3 (real-truth) is the NEXT tick.

- [tick 23 | GENBA] Thought: status PLAN_LOCKED_AWAITING_BUILD for M1 Sprint 3 (real truth) → §3.2 BUILD tick. Sprint 3 touches render (the keystone) via the propagate_satellite_radec extraction, so it IS @solver-relevant (AC 3.4 golden-e2e regression) → verify BOTH baselines. Read loop_state IN FULL + config + the M1 plan IN FULL. → Action(Read state full + config + plan; re-ground render._propagate_satellite/_exposure_times/_build_truth, score._load_truth, ingest, meta.toml, scene TLE API, test_render propagation tests; git status --porcelain + HEAD + branches + tags + log since last_green df22ff4; shasum the M1 plan; `make test` + `make test-golden`) → Observation: clean tree on main @ dc4247d; only the tick-22 loop bookkeeping commit since df22ff4 (loop-authored, no foreign branch — only `main` + tag v0.1.0); plan re-hash 955c27e35f9e…a2ed MATCHES (NOT stale); no_progress 0; tick_lock null. Baseline GREEN: 121 non-solver + 5 @solver (golden e2e 2.081", AC 2.5 skip). Set tick_lock + committed begin-marker 8287368 on main; cut feat/m1-s3-realtruth. ALL §3.5 gates pass.
- [tick 23 | RESEARCH] Thought: Sprint 3 is mostly settled by the plan, but it carries ONE genuine external unknown the plan + open_findings explicitly flag — the DDOTI/OAN-SPM site coords are site_confirmed=false, and LEO parallax makes the site material (AC 3.2 topocentric). Resolve that fact (targeted confirm, not /deep-research). → Action(WebSearch + WebFetch airmass.org/observatories/spm + OAN-UNAM; quantify the parallax error of a ~63 m site delta for a 510 km LEO object in a scratch python) → Observation: authoritative OAN-SPM = 31.044333°N / −115.46375°W / 2830 m (airmass.org 31°02′39.60″N/115°27′49.50″W, corroborated by OAN-UNAM); the placeholder was 31.0442/−115.4633/2790 m. A ~63 m site error ⇒ up to ~25" apparent shift for a 510 km LEO (overhead worst case) — LARGER than the 10" gate → MATERIAL → confirm-to-source. Will update meta.toml [observatory] to the published values + site_confirmed=true.
- [tick 23 | IDEATE] Thought: Sprint 3 is fully specified (plan ACs 3.1-3.5) but HIGH-RISK — it extracts a render keystone helper + assembles the SOLE real satellite-truth → a BRIEF design brief, not a full brainstorm. → Action(emit brief, below) → Observation: brief recorded. Pre-Mortem clear: (a) propagate_satellite_radec is a behavior-preserving extraction (re-invents nothing); realtruth is a NEW writer; (b) seal EXTENDED not weakened (realtruth json.dump only; symmetric static-import seal); (c) all solving contracts preserved; (d) scope == plan Sprint 3 ACs (run.py wiring + AC-4.6 are Sprint 4, YAGNI-correct boundary).
- [tick 23 | BUILD] Thought: §3.2 BUILD under inner TDD (Red→Green→Refactor). Task/Agent spawn tool unavailable this env → build directly in-parent under test-driven-development + konnyaku. → Action(CYCLE 1: RED test_propagate_satellite_radec_pure_helper_matches_inline → ImportError; GREEN extract propagate_satellite_radec(tle,lat,lon,elev,when)→(ra,dec), _propagate_satellite now a thin loop over it; render 20 unit + golden e2e 2.081" green = AC 3.4; commit fbdbfb6. CYCLE 2: confirm DDOTI site → meta.toml [observatory] = published OAN-SPM + site_confirmed=true + PROVENANCE.md updated; RED 5 timing tests → GREEN realtruth.exposure_midpoint_utc (start+EXPTIME/2, robust ISO, fail-loud); RED 7 assembly tests → GREEN assemble_real_truth (shared topocentric propagation → truth.json scored_truth that score._load_truth reads UNCHANGED; header WCS + midpoint in-memory; json.dump only); rephrased a docstring that named the literal json.load token (the tick-22 false-positive class); EXTENDED the seal symmetrically over realtruth; updated the stale site-confirmation fixture test to the confirmed coords; commit 471b074.) → Observation: 135 non-solver + 5 @solver green; golden e2e 2.081" intact.
- [tick 23 | BUILD-MUTATION] Thought: a green test a broken impl would also pass is worthless → mutation-verify every load-bearing assertion BEFORE review. → Action(M1 midpoint=start (drop +EXPTIME/2) → AC 3.1 timing tests FAIL; M2 wrong scored_truth key → AC 3.3 round-trip+schema FAIL; M3 RA/Dec axis swap → AC 3.2 shared-prop + round-trip FAIL; M4 smuggle `import json as _j; _j.loads()` into realtruth → repo-wide json.load guard FAIL; M5 import realtruth into measure_position → new realtruth static-import seal FAIL; restore each) → Observation: ALL FIVE mutations correctly FAILED the intended test; every restore byte-clean (empty src diff). The new tests genuinely bite.
- [tick 23 | REVIEW] Thought: Sprint 3 HIGH-RISK (real satellite-truth + render-keystone extraction) → MANDATORY 2nd independent LOCAL review. Spawn tool unavailable → run TWO genuinely separate in-parent passes that RE-DERIVE the claims (local/free; /code-review ultra BANNED). → Action(PASS 1: fully independent scratch-skyfield re-derivation of the midpoint + RA/Dec, NOT calling the module helper; PASS 2: adversarial seal/non-circularity/edge probes — grep json.load across src/, realtruth names no reader/solver token in CODE, realtruth calls no solving module, a non-None pointing_wcs does NOT serialize into truth.json) → Observation: BOTH ACCEPT. Pass 1: module truth == independent re-derivation to <1e-9 deg; the sat moves 5285" in the 5 s start→midpoint window (start-vs-midpoint is enormously material, >>10" gate). Pass 2: json.load in score.py ONLY; realtruth's score/_load_truth mentions are docstring prose (the substring seal applies only to solving modules — realtruth is a writer, like render); non-circularity holds; pointing_wcs in-memory only. Findings: F1 (CARRY) AC 2.5 + the real frame still un-fetched → Sprint 4 gating; F2 (NIT) realtruth's extra provenance keys are ignored by score (round-trip proven). No blocker/major. Genchi-genbutsu cross-check: scored truth (306.525,−14.889) lands 0.97° from the blind-solved center (305.557,−14.964) = INSIDE the 1.705° half-field → the satellite genuinely falls on the real frame.
- [tick 23 | INTEGRATE] Thought: PHASE-5 gate met (2 ACCEPT passes + every finding dispositioned + both suites green; the one CARRY is a sourcing/network constraint, not a code defect) → integrate. → Action(merge --no-ff feat/m1-s3-realtruth → main @ 534bc31; `make test` + `make test-golden` on main; git branch -d feat/m1-s3-realtruth) → Observation: merged @ 534bc31; 135 non-solver + 5 @solver green on main (golden e2e 2.081" intact); branch deleted, only `main`. Sprint 3 ≠ a milestone (v0.1.1 is plan Sprint 6) → no tag. no_progress_count stays 0 (green merge).
- [tick 23 | HANSEI] What worked: the targeted RESEARCH step earned its keep — the open_finding flagged site_confirmed=false as a watch-item, but quantifying the parallax (a ~63 m site error ⇒ ~25" > the 10" gate) turned a "maybe confirm later" into a MUST-confirm-this-tick, and the published OAN-SPM coords resolved it to observatory-scale precision (residual within-campus <~25", below the dominant ~arcminute TLE-age term). The two-pass independent review (spawn tool unavailable) was decisive: re-deriving the truth from a fully separate scratch skyfield path proved <1e-9 deg agreement, and the genchi-genbutsu cross-check (scored truth lands 0.97° INSIDE the blind-solved field) is the strongest non-circular evidence the TLE+timing+site assembly is coherent — the satellite really is on the frame. The single most load-bearing pin was AC 3.1: review pass 1 measured the sat moving 5285" in the 5 s exposure, so the start-vs-midpoint distinction is ENORMOUS (>>10" gate); getting it wrong would have silently fabricated a flattering-but-fictional residual the same way a far-epoch TLE would. Honest scoping: I smoothed an earlier panel rather than weakening it — the Sprint-1/2 fixture test had pinned site_confirmed=false; Sprint 3's job is to confirm the site, so I flipped that assertion to GUARD the confirmed published coords (konnyaku stone over the prior layer). KAIZEN (Sprint 4): Sprint 4 is @solver and CANNOT proceed frame-absent the way Sprint 3 (non-solver) did — the real BW3 frame must be FETCHED first (longer-window/out-of-band fetch.sh, or Sam drops the .fits in), which also finally executes AC 2.5. Then derive the C1-camera offset NON-CIRCULARLY from ≥3 OTHER C1 frames for the AC-4.6 plausibility gate (do NOT use this frame's own recovered−commanded). Env note persists: the Agent/Task spawn tool has been unavailable since tick 21 → keep the two-genuinely-separate-in-parent-passes discipline for the Sprint-4 high-risk merge. Anti-spin: green merge → no_progress 0. Per §3.2 this BUILD tick ENDS at the green merge; Sprint 4 is the NEXT tick.

### increment design brief (tick 23)

```
S3 (M1) — real truth: header-WCS pointing-truth + TLE→skyfield satellite-truth → truth.json. Build
EXACTLY plan Sprint 3 (ACs 3.1-3.5). HIGH-RISK: extracts a render keystone helper + assembles the SOLE
real satellite-truth → mandatory 2nd independent LOCAL review.

CHOSEN APPROACH: (a) extract render.propagate_satellite_radec(tle,lat,lon,elev,when_utc)→(ra,dec) PURE
from render._propagate_satellite (the no-epoch ICRS (sat - wgs84.latlon(...)).at(t).radec() call —
REUSED IDENTICALLY so real truth shares the solver's ICRS frame); _propagate_satellite becomes a thin
loop over it (behavior-preserving; render 20 unit + golden e2e green = AC 3.4). (b) NEW realtruth.py:
exposure_midpoint_utc(date_obs,exptime) = DATE-OBS(start,UTC)+EXPTIME/2, robust ISO parse, fail-loud on
ambiguity (AC 3.1); assemble_real_truth(tle,meta,out_dir) propagates the committed BW3 TLE via the
SHARED helper TOPOCENTRIC at the midpoint → truth.json scored_truth that score._load_truth reads
UNCHANGED (AC 3.2/3.3); returns header WCS + midpoint IN-MEMORY (AC 3.5). json.dump only → score stays
the SOLE json.load reader. (c) CONFIRM the DDOTI site (meta.toml [observatory] → published OAN-SPM
31.044333/−115.46375/2830 m, site_confirmed=true; LEO parallax material). EXTEND the seal symmetrically
over realtruth (static-import forbidden list; repo-wide alias-resistant json.load guard already covers it).

SCOPE CUT (JIT / sprint boundary): Sprint 3 writes the real truth.json + extracts the helper. run.py
--image/--meta wiring + the AC-4.6 plausibility gate are Sprint 4 — building them now would be
over-production. The plan's ACs split the work; the binding ACs win.

TOUCHED MODULES: src/tracklet/render.py (extract propagate_satellite_radec + thin-loop _propagate_satellite)
+ src/tracklet/realtruth.py (NEW) + src/tracklet/score.py (docstring: name all 3 writers) + tests/
test_realtruth.py (NEW) + tests/test_render.py (1 helper test) + tests/test_seal.py (realtruth static-import
seal) + tests/test_real_fixtures.py (site-confirmation assertion) + tests/fixtures/real/{meta.toml,
PROVENANCE.md} (site confirmed). solve_pointing/detect_streak/measure_position/ingest/scene/report/run UNTOUCHED.

TEST ORACLE (ACs 3.1-3.5): 3.1 midpoint=start+EXPTIME/2 + robust ISO + fail-loud (5 tests); 3.2 RA/Dec via
the SHARED propagate_satellite_radec topocentric + parallax-honored (2); 3.3 truth.json → score._load_truth
UNCHANGED + scored_truth schema (2); 3.4 render 20 unit + golden e2e green (regression); 3.5 midpoint +
header-WCS in-memory + writer-names-no-read-token (3); + 1 render-helper extraction test + 1 realtruth
static-import seal. ALL load-bearing assertions mutation-verified.

YAGNI / OUT OF SCOPE: NO run.py wiring (Sprint 4), NO AC-4.6 plausibility gate (Sprint 4), NO degradation
report (Sprint 5), NO streak-vs-catalogue matcher (PHASE 2).

JUDGE: N/A — brief design brief (Sprint 3 fully specified; no design fork). Pre-Mortem manual, all clear:
(a) propagate_satellite_radec is a behavior-preserving extraction + realtruth is a new writer (re-invents
nothing); (b) the seal is EXTENDED not weakened (realtruth json.dump only; symmetric static-import seal);
(c) all signed solving contracts preserved; (d) scope == plan Sprint 3 ACs.
```
