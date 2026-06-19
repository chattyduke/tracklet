---
status: applied  # 2026-06-20 — added [artifacts] convention (run-output dirs + large-generated globs + BUILD-phase add-ignore-AND-verify-it-fires Poka-Yoke) to .autobuild/config.md; config gate PASSED (config.load_config dry-run validates); invariant-core SHA unchanged.
target: project-config
pathology_class: constituent-skill
key: generated-output-gitignore-verify-pokayoke
date: 2026-06-19
cites: [tick 24 HANSEI, tick 27 BUILD, tick 27 HANSEI]
severity: medium
---
# Large generated outputs were committable by default and the gitignore fix was re-improvised twice, once defectively

**Pathology.** Large generated artifacts were committable by default and the loop had to hand-add gitignore rules twice, once with a silent defect. The same artifact-hygiene class (generated big files leaking into history) recurred across the milestone with no engine-level guard, and — worse — a gitignore rule that does not actually match gives false confidence, which only a touch-and-check mutation probe caught.

**Evidence (cited ticks).**
- tick 24 HANSEI — "*.fits.fz is now gitignored (it was committable; the 17 MB frame could have bloated the repo)" — an ad-hoc rule added mid-build.
- tick 27 BUILD — ignoring `out_real/` (the 76 MB documented run output) had a DEFECTIVE first cut: an inline `out_real/   # comment` is not a git comment, so the literal pattern silently did not match; caught by a touch-and-check mutation probe (`touch out_real/test.md` → still `??`), then fixed by moving the comment to its own line.
- tick 27 HANSEI — names the lesson: "a Poka-Yoke that does not actually fire is worse than none (false confidence) — verify the Poka-Yoke itself, don't assume it."

**Proposed change.** Add an `[artifacts]` convention to `.autobuild/config.md` declaring the run/output directory and large generated extensions (`out/`, `out_real/`, `*.fits`, `*.fits.fz`) as must-be-ignored, plus a one-line BUILD-phase Poka-Yoke reminder: whenever a tick introduces a new generated-output path, add the ignore AND verify it fires (`git check-ignore` / touch-and-check) before commit — because an ignore rule that does not actually match is worse than none. This stops the recurring leak class and the defective-inline-comment failure mode at source instead of per-tick.

**Does NOT weaken the immutable core because.** It is an additive artifact-hygiene convention in project-config plus a verify-the-Poka-Yoke reminder; it touches no safety rail and REINFORCES the clean-tree / byte-identical-reproduce discipline. No sealed file is edited; no effect on the seal, non-circularity, cost guard, plan-lock, no-auto-push, no-build-on-red, the no_progress counter, or the hash chain.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
