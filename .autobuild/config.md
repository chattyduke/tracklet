# tracklet — `/autobuild-loop` per-project config

This is the ONLY project-specific input the `/autobuild-loop` engine reads. The engine is
generic; everything tracklet-specific lives in the toml block below. Runtime state lives beside
this file at `.autobuild/loop_state.md` (migrated from `.tracklet/` in S8 of the autobuild-loop
upgrade — see [[project_autobuild_loop]]). An absent or schema-invalid config is an Andon halt.

```toml
[project]
name = "tracklet"
repo_path = "/Users/samuelleishman/tracklet"
# DEPRECATED legacy global pointer — SUPERSEDED by per-milestone plan_path (in the [[milestones]] ladder
# below). The schema requires a NON-EMPTY string, so this holds the LAST-active milestone's plan as a
# backward-compatible fallback; once the milestone-boundary tick class lands, the engine derives the ACTIVE
# plan from current_milestone's plan_path and this field is vestigial. The active milestone M2 is UNPLANNED
# (its plan_path = "") → it needs a FRESH planning tick. (M0 @ v0.1.0; M1 @ v0.1.1.)
# Per-milestone-plan-map card 2026-06-19-per-milestone-plan-map (config gate: schema-valid dry-run).
approved_plan_path = "/Users/samuelleishman/.claude/plans/plan-the-m1-real-image-snappy-bunny.md"

[poka_yoke]
# tracklet's sealed-truth / non-circularity invariant. render is the SOLE writer of truth.json;
# image.fits ships WCS-free. The three solving modules (solve_pointing, detect_streak,
# measure_position) NEVER read truth — solve is BLIND (no RA/Dec seed), detection reads only the
# image. score is the only reader of truth. So the recovered RA/Dec is graded against a sealed
# truth it could not have seen — the arcsec residual is a real non-circular measurement.
seal = "sealed-truth / non-circularity: render is the sole writer of truth.json and image.fits is WCS-free; solve_pointing/detect_streak/measure_position never read truth (solve is blind, detect reads only the image); only score reads truth — the recovered RA/Dec is graded against a truth it could not see"

[optimizer]
# /autobuild-optimize runs only at a milestone boundary, never per-tick.
cadence = "milestone-boundary"

# The real milestone ladder (M0 synthetic core -> M_final V1.0). Lowest first.
# Each rung binds to its own /ultraplan plan via plan_path (+ plan_sha256 when known). The engine derives
# the ACTIVE plan from current_milestone, so a milestone boundary needs NO manual global repoint. A rung
# with plan_path = "" is the schema-checkable "needs a fresh planning tick" state. Keep each dod a PURE
# definition-of-done with NO embedded plan/sprint pointers (those live in plan_path).
[[milestones]]
id = "M0"
plan_path = "/Users/samuelleishman/.claude/plans/lucky-dazzling-parasol.md"
plan_sha256 = "d7237cddd2363b869e3d888dfafc801932db3923adf924a37b86addba9f73f07"
dod = "synthetic-from-real-data pipeline green end-to-end (S0-S7): render -> blind plate-solve -> detect_streak -> measure_position -> score yields an arcsec residual < threshold vs SEALED truth; the 3 seal tests pass; the @solver golden-e2e DoD gate passes (actual residual number always reported); README reproduce/footprint/uninstall + licences documented; tag v0.1.0"

[[milestones]]
id = "M1"
plan_path = "/Users/samuelleishman/.claude/plans/plan-the-m1-real-image-snappy-bunny.md"
plan_sha256 = "955c27e35f9ea3627d3edbf6f276105b5d9b1d82b34e0e3d12543062d9b5a2ed"
dod = "real image: run the full pipeline on a genuine telescope / all-sky frame (not synthetic) and recover a real satellite streak's RA/Dec with a reported residual; a human-approval andon gate applies at Sprint 1 (confirm frame + NORAD id + provenance before Sprint 2); tag v0.1.1"

[[milestones]]
id = "M2"
plan_path = ""  # unset — M2 needs a FRESH planning tick (the active milestone as of 2026-06-19)
dod = "packaging / CI / pip: stranger-reproducible — clone -> install -> reproduce the arcsec residual unaided; CI green on a clean machine; pip-installable"

[[milestones]]
id = "M3"
plan_path = ""  # unset — JIT, planned when this rung is reached
dod = "V0.2 capability — JIT: Sam picks the next capability when this rung is reached (not pre-specified)"

[[milestones]]
id = "M_final"
plan_path = ""  # unset — planned when this rung is reached
dod = "V1.0 finished product: stranger-reproducible end-to-end optical-SDA proof (clone -> install -> reproduce the arcsec residual unaided), with the sealed-truth / non-circularity boundary verified by the REVIEW pass"

[green]
# The real pytest markers tracklet uses (from loop_state green_suites). Non-solver is the fast
# baseline; the @solver suite exercises the live blind solve-field + 4100 indexes (S0-installed).
commands = ["pytest -m \"not solver\"", "pytest -m solver"]
```
