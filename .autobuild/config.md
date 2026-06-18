# tracklet — `/autobuild-loop` per-project config

This is the ONLY project-specific input the `/autobuild-loop` engine reads. The engine is
generic; everything tracklet-specific lives in the toml block below. Runtime state lives beside
this file at `.autobuild/loop_state.md` (migrated from `.tracklet/` in S8 of the autobuild-loop
upgrade — see [[project_autobuild_loop]]). An absent or schema-invalid config is an Andon halt.

```toml
[project]
name = "tracklet"
repo_path = "/Users/samuelleishman/tracklet"
# The human-approved /ultraplan build plan for the ACTIVE milestone (absolute — it lives outside the
# repo, in the plan archive). Repointed M0->M1 on milestone transition (tick 18, 2026-06-18): M0 shipped
# against lucky-dazzling-parasol.md (tag v0.1.0); M1 has its own dedicated, human-signed contract below.
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

# The real milestone ladder from lucky-dazzling-parasol.md + project memory (M0 synthetic core ->
# M_final V1.0). Lowest first.
[[milestones]]
id = "M0"
dod = "synthetic-from-real-data pipeline green end-to-end (S0-S7): render -> blind plate-solve -> detect_streak -> measure_position -> score yields an arcsec residual < threshold vs SEALED truth; the 3 seal tests pass; the @solver golden-e2e DoD gate passes (actual residual number always reported); README reproduce/footprint/uninstall + licences documented; tag v0.1.0"

[[milestones]]
id = "M1"
dod = "real image: run the full pipeline on a genuine telescope / all-sky frame (not synthetic) and recover a real satellite streak's RA/Dec with a reported residual — the M1 real-image stretch (see plan-the-m1-real-image-snappy-bunny.md, the dedicated M1 contract that supersedes the M0 plan's Sprint-8 sketch; target tag v0.1.1), a human-approval andon gate applies at Sprint 1 (confirm frame + NORAD id + provenance before Sprint 2)"

[[milestones]]
id = "M2"
dod = "packaging / CI / pip: stranger-reproducible — clone -> install -> reproduce the arcsec residual unaided; CI green on a clean machine; pip-installable"

[[milestones]]
id = "M3"
dod = "V0.2 capability — JIT: Sam picks the next capability when this rung is reached (not pre-specified)"

[[milestones]]
id = "M_final"
dod = "V1.0 finished product: stranger-reproducible end-to-end optical-SDA proof (clone -> install -> reproduce the arcsec residual unaided), with the sealed-truth / non-circularity boundary verified by the REVIEW pass"

[green]
# The real pytest markers tracklet uses (from loop_state green_suites). Non-solver is the fast
# baseline; the @solver suite exercises the live blind solve-field + 4100 indexes (S0-installed).
commands = ["pytest -m \"not solver\"", "pytest -m solver"]
```
