---
status: proposed
target: project-config
pathology_class: constituent-skill
key: no-header-wcs-empirical-offset-pattern
date: 2026-06-19
cites: [tick 22 BUILD, tick 24 BUILD, tick 25 BUILD]
severity: medium
---
# The no-header-WCS empirical camera-offset adaptation was invented on the fly across three ticks and lives only in scattered prose

**Pathology.** The chosen real frame (DDOTI) carried NO header WCS, which the AC-4.6 plausibility gate had assumed; the loop had to invent a non-circular field-lock adaptation on the fly across three ticks. The genuinely reusable pattern — derive the per-camera pointing offset EMPIRICALLY from other frames of the same camera, never from the target frame's own recovered-minus-commanded, and require a measurable-distinctness witness — emerged through trial and lives only in scattered HANSEI prose and meta.toml, undocumented as config guidance for the next no-WCS frame.

**Evidence (cited ticks).**
- tick 22 BUILD — confirmed the real frame header has "NO header WCS (0 keys)" (STRCURA/STRCUDE commanded pointing only), contradicting the AC-4.6 assumption.
- tick 24 BUILD — the AC-4.6 gate MEASURED the blind-recovered C1 field sits 2.25° from the commanded mount pointing and correctly REFUSED to emit a residual on commanded-only.
- tick 25 BUILD — derived the C1 camera offset from 3 OTHER same-camera frames (mean recovered-minus-commanded, scatter 0.00011°), and proved non-circularity by showing the committed offset is measurably distinct (~0.7″) from the target frame's own recovered-minus-commanded.

**Proposed change.** Record, in `.autobuild/config.md` (seal / acquisition notes), the no-header-WCS fallback as a sanctioned, non-circular pattern: when a real frame lacks a header WCS, derive the per-camera pointing offset EMPIRICALLY from >=3 OTHER frames of the SAME camera/instrument (mean recovered-minus-commanded, report the scatter), and NEVER from the target frame's own recovered-minus-commanded; the field-lock gate then checks blind-recovered-plus-offset against commanded within the half-field tolerance. Note the mandatory non-circularity witness (the committed offset must differ measurably from the target's own delta) as the acceptance check. This turns a three-tick improvisation into a documented, reviewable adaptation any future no-WCS frame can reuse.

**Does NOT weaken the immutable core because.** It codifies and STRENGTHENS the non-circularity rail (offset derived from OTHER frames + a measurable-distinctness witness) — the opposite of weakening the seal. The AC-4.6 tolerance itself stays untouched (the tick-25 review confirmed realgate.py byte-identical). No sealed file is edited; no impact on the cost guard, plan-lock, no-auto-push, no-build-on-red, the no_progress counter, or the hash chain.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
