---
status: approved
target: generic-skill
pathology_class: loop-itself
key: milestone-boundary-fresh-plan-tick-class
date: 2026-06-19
cites: [tick 18 PLAN, tick 18 GENBA, tick 27 GENBA]
severity: high
---
# Milestone-boundary FRESH planning tick is under-specified vs sprint-boundary ticks, so the plan/config repoint is ad-hoc prose

**Pathology.** The §3.2 tick-boundary table has three rows (FRESH, PLAN_LOCKED, FIX) and does not distinguish a within-milestone sprint advance from a milestone-boundary advance. At a milestone boundary the loop must do extra, un-templated work inside a generic FRESH tick: repoint BOTH `config.approved_plan_path` AND `loop_state.plan_file/plan_sha256` from the consumed plan to the new milestone's plan, and re-record the SHA so the §4-#3 stale-plan Andon applies to the right plan. This load-bearing repoint (get it wrong and the next BUILD tick's SHA gate bites the wrong plan) is handled by narrative prose each time rather than a defined tick class, and the same hazard is now live again at the M1→M2 boundary.

**Evidence (cited ticks).**
- tick 18 PLAN — "the milestone advanced M0→M1, so the binding plan changes: repoint BOTH config.approved_plan_path AND loop_state.plan_file/plan_sha256 to the M1 plan ... leaving config pointed at the COMPLETED M0 plan would mis-point the next tick" (the repoint done by hand, plus a stale "(plan S8)" dod pointer corrected as a side-task).
- tick 18 GENBA — observed the carried state was "internally consistent, just pointed at the COMPLETED M0 plan", i.e. a deliberately-stale pin straddling the boundary.
- tick 27 GENBA — the same condition recurs at M1→M2: the frontmatter notes "plan_sha256 below still pins the CONSUMED M1 plan; the FRESH tick will repoint config.approved_plan_path to the new M2 plan" — the loop is carrying a deliberately-stale plan_sha256 across the boundary, the exact condition §4-#3 is designed to halt on.

**Proposed change.** Add a MILESTONE-BOUNDARY sub-classification of the FRESH tick to §3.2 in `~/.claude/skills/autobuild-loop/references/phases.md`, with an explicit ordered checklist: (1) the just-completed milestone's plan_sha256 is EXPECTED-stale at the boundary — a milestone-advance is the ONE sanctioned exception to §4-#3, gated on `milestone_complete=TRUE`, so the stale-plan Andon does not fire spuriously; (2) repoint `config.approved_plan_path` AND `loop_state.plan_file` in the SAME plan-lock commit; (3) re-record `plan_sha256` against the NEW plan and re-verify before the next BUILD; (4) fire the optimizer if `cadence='milestone-boundary'`. This makes the repoint mechanical and Poka-Yoked rather than prose-driven, and removes the latent "carrying a stale plan_sha256 on purpose" ambiguity tick 27 sits in.

**Does NOT weaken the immutable core because.** It PRESERVES the §4-#3 stale-plan HARD-STOP and the ExitPlanMode plan-lock boundary, and only adds a precise `milestone_complete`-gated carve-out for the one legitimate boundary repoint — the stale-plan Andon keeps firing in every other case. It touches the §3.2 table + boundary checklist in the generic engine, none of the three sealed files.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
