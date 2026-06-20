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
approved_plan_path = "/Users/samuelleishman/.claude/plans/plan-the-m2-packaging-glossy-lighthouse.md"

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
plan_path = "/Users/samuelleishman/.claude/plans/plan-the-m2-packaging-glossy-lighthouse.md"
plan_sha256 = "2d138b883efa9949c8c104b803bfb5204097522399f4c10e20d61954b856d008"  # LOCKED at the M1→M2 boundary (tick 28); out-of-band /ultraplan plan (3 adversarial critic rounds, converged 4/5/5/5/5)
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

# Applied from card 2026-06-19-generated-output-gitignore-verify-pokayoke (project-config; config gate:
# schema-valid dry-run). Large generated artifacts must be gitignored, AND an ignore rule must be VERIFIED
# to actually fire — a Poka-Yoke that does not fire is worse than none (false confidence): tick 27 caught an
# inline `out_real/  # comment` that is not a git comment and so silently did not match. Reinforces the
# clean-tree / byte-identical-reproduce discipline; touches no safety rail.
[artifacts]
run_output_dirs = ["out/", "out_real/"]
large_generated_globs = ["*.fits", "*.fits.fz"]
build_phase_pokayoke = "When a tick introduces a NEW generated-output path, add the .gitignore rule AND verify it fires (git check-ignore <path>, or touch-and-check that the file reads as ignored) BEFORE commit — an ignore rule that does not actually match is worse than none."

# Applied from card 2026-06-19-large-artifact-stream-extract-pokayoke (project-config; config gate:
# schema-valid dry-run). The durable fetch rule the loop paid three ticks (22/24/25) to learn. Strengthens
# the SHA-pin / byte-identical-reproduce discipline; touches no safety rail.
[acquisition]
large_remote_archive_rule = "When sourcing data from a large remote archive, NEVER download the whole archive to disk. Stream and extract only the needed member(s) (tar -xzO / HTTP range-read); pin and verify a per-member SHA256; pay any deep-archive seek ONCE via a single-pass multi-member extraction — NOT parallel range-reads (they stalled at 0 bytes), NOT per-member serial re-seeks (~25 min each)."
member_size_hint = "DDOTI FITS member ~17.5 MB; the whole Zenodo archive (~2.4 GB) must never hit the working tree."

# Applied from card 2026-06-19-no-header-wcs-empirical-offset-pattern (project-config; config gate:
# schema-valid dry-run). Codifies and STRENGTHENS the non-circularity rail (the seal): the no-header-WCS
# field-lock fallback derives the camera offset from OTHER frames + requires a measurable-distinctness
# witness. Does NOT touch the [poka_yoke].seal rail; the AC-4.6 tolerance is unchanged (realgate.py
# byte-identical per the tick-25 review).
[seal_notes]
no_header_wcs_offset_pattern = "When a real frame lacks a header WCS, derive the per-camera pointing offset EMPIRICALLY from >=3 OTHER frames of the SAME camera/instrument (mean recovered-minus-commanded, report the scatter) — NEVER from the target frame's own recovered-minus-commanded. The field-lock gate then checks blind-recovered-plus-offset against the commanded pointing within the half-field tolerance."
non_circularity_witness = "MANDATORY acceptance check: the committed offset must differ MEASURABLY from the target frame's own recovered-minus-commanded delta (M1: ~0.7 arcsec distinct) — this proves the offset was not laundered from the target itself."

# Applied from card 2026-06-19-real-frame-acquisition-checklist (project-config; config gate:
# schema-valid dry-run). Surfaces the four real-frame prerequisites at PLAN time so frame+TLE acquisition
# is an explicit human-gated precondition, not a mid-BUILD surprise (M1 burned two andon halts, ticks 19/20).
# Documentation-only; REINFORCES (never relaxes) the non-circularity / no-correlator rail (identity must be
# EXTERNAL, never loop-derived). Applies to M1 and any future real-data milestone.
[real_frame_acquisition]
checklist = "BEFORE a real-image sprint starts, ONE downloadable frame must carry ALL FOUR: (a) retrievable FITS (byte-identical via SHA-pinned stream); (b) a pointing reference (header WCS OR documented commanded-pointing + empirical camera offset, see [seal_notes]); (c) precise UTC (DATE-OBS start + EXPTIME); (d) an EXTERNALLY-established NORAD identity (dataset-carried, NOT loop-correlated)."
structural_blocker = "FITS-publishers and identity-publishers are largely DISJOINT corpora (datasets ship FITS without NORAD identity; identity papers ship no retrievable FITS+WCS+UTC), and historical TLE-by-date requires a credentialed Space-Track pull (CelesTrak gp-history 404s for the public). Treat frame + historical-TLE acquisition as a human-gated prerequisite raised at PLAN time."
```
