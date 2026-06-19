---
status: applied  # 2026-06-19 — config edited (per-milestone plan_path + plan_sha256, dod prose cleaned, approved_plan_path deprecated→fallback); config gate PASSED (config.load_config dry-run validates). Engine-side derivation of the active plan from current_milestone.plan_path lands with the companion skill card (milestone-boundary-fresh-plan-tick-class).
target: project-config
pathology_class: loop-itself
key: per-milestone-plan-map
date: 2026-06-19
cites: [tick 18 PLAN, tick 18 GENBA, tick 27 GENBA, tick 27 HANSEI]
severity: high
---
# Single global approved_plan_path + prose plan-pointers in dod strings force a manual multi-field repoint at every milestone boundary

**Pathology.** `.autobuild/config.md` carries a SINGLE global `approved_plan_path` (line 15) plus a single `loop_state.plan_file/plan_sha256`, and the milestone `dod` text embeds plan references as free prose (line 37: the M1 dod still names "the M0 plan's Sprint-8 sketch ... target tag v0.1.1"). There is no structured binding from a milestone id to its plan, so every milestone transition forces a manual, multi-place hand-edit to repoint the active plan AND a prose pointer that no schema check can see goes stale across the transition. Both facets are the same root: the plan binding is not a structured per-milestone field.

**Evidence (cited ticks).**
- tick 18 PLAN — repointed by hand: "repoint BOTH config.approved_plan_path AND loop_state.plan_file/plan_sha256 to the M1 plan", AND separately had to "correct the M1-dod '(plan S8)' stale pointer" as a side-task — a prose pointer invisible to any schema check, fixed only because it was noticed.
- tick 18 GENBA — confirmed the global pointer straddled the boundary pointing at the COMPLETED M0 plan.
- tick 27 GENBA — the identical gap is live again at M1→M2 with no automation: the global `approved_plan_path` still points at the consumed M1 plan and must be hand-repointed.
- tick 27 HANSEI — flags the M2 FRESH planning tick must repoint `config.approved_plan_path` to the new M2 plan and re-record the SHA, as a manual to-do.

**Proposed change.** Extend the config schema in `.autobuild/config.md` so each `[[milestones]]` entry carries its own structured `plan_path` (+ optional `plan_sha256`) field, and have the engine derive the active plan from `current_milestone` rather than from a single global `approved_plan_path` (the global becomes a derived view or is dropped). Keep each `dod` string a pure definition-of-done statement with NO embedded plan/sprint pointers — the plan reference moves to the structured `plan_path`. Optionally add a config-load assertion that `dod` text contains no `(plan S...)` / `Sprint-N sketch` substring, so a stale cross-plan prose pointer fails the schema-valid check (an Andon at config load) instead of riding silently into the next milestone. A milestone whose `plan_path` is unset is then a clear, schema-checkable "needs a fresh planning tick" state — exactly tick 27's M2 condition.

**Does NOT weaken the immutable core because.** It touches only the plan-binding schema in `.autobuild/config.md` plus the engine's plan-resolution read path. A per-milestone `plan_sha256` STRENGTHENS the §4-#3 stale-plan gate by binding it to the right plan automatically (tick 18 had to re-record the SHA by hand for exactly this reason). The ExitPlanMode/plan-lock boundary, no-auto-push, the seal, and the dod's actual gate semantics (residual < threshold, seal tests pass) are all preserved verbatim; no sealed file is edited.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
