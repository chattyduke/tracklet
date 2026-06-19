---
status: proposed
target: generic-skill
pathology_class: loop-itself
key: deferred-fetch-carry-not-spin
date: 2026-06-19
cites: [tick 22 REVIEW, tick 24 BUILD, tick 24 HANSEI, tick 25 BUILD]
severity: medium
---
# A long external fetch has no engine-level home, so the same expensive fetch is re-derived/re-attempted across ticks and once forced a binding test to SKIP

**Pathology.** When a required artifact needs a fetch longer than the comfortable single-tick window, the engine has no notion of a long-running side-task that must survive across ticks. The loop improvised differently each time: a forced SKIP of a binding test (tick 22), an unbounded-wait stall (tick 24), and a re-derived recipe (tick 25). The right discipline — bounded window, carry-not-spin, resolve out-of-band before the dependent @solver test, and never silently pass a skipped binding test — emerged only by trial and is not written into the engine's tick-boundary guidance, and the no_progress anti-spin rail risks being burned by re-attempting the same fetch.

**Evidence (cited ticks).**
- tick 22 REVIEW — F1: AC 2.5 (the binding Sprint-1 confirmation) was SKIPPED because "the frame fetch exceeded the 600s curl window"; the normalized real image was left unproven to solve+detect for two more ticks.
- tick 24 BUILD — a 3-way-parallel fetch STALLED at 0 bytes for 8 min; a single longer-window stream finally succeeded in ~3 min and AC 2.5 was executed.
- tick 24 HANSEI — explicitly: do NOT block a tick on unbounded network wait (Muri); land the solid increment and carry the network item.
- tick 25 BUILD — the deep-archive fetch was re-derived again (single-pass ~30 min) for the 3 offset frames, re-reasoning the recipe rather than consulting a recorded slot.

**Proposed change.** Add to the autobuild-loop engine (`~/.claude/skills/autobuild-loop/references/phases.md` BUILD/Andon section + `references/state-schema.md`) a lightweight "deferred external-fetch" state slot in `loop_state.md`: when a tick discovers a required artifact needs a fetch longer than the comfortable single-tick window, it records the exact reproducible fetch recipe + the pinned member SHA + a `fetch-pending` marker ONCE, and subsequent ticks consult that slot instead of re-deriving the recipe. Add a short guidance note: when a required fetch cannot complete in-window, do NOT (a) spin re-running it toward the no_progress gate, nor (b) block on unbounded wait — land any independently-green increment, carry the fetch as a named network blocker, and resolve it out-of-band before the dependent @solver test; a fetch-skipped binding test is a carried item to surface to the human, NEVER a silent pass.

**Does NOT weaken the immutable core because.** It preserves and clarifies (does not weaken) the no-build-on-red and no_progress anti-spin rails — it explicitly says carry-not-spin and never silently pass a skipped binding test. It deliberately AVOIDS any autonomous re-launch or auto-scheduling (which would conflict with the human-mediated model) and adds no silent auto-stop. It touches the generic engine's state schema + §3.x guidance, none of the three sealed files.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
