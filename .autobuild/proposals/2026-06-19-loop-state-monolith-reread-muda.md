---
status: proposed
target: generic-skill
pathology_class: loop-itself
key: loop-state-monolith-reread-muda
date: 2026-06-19
cites: [tick 22 GENBA, tick 23 GENBA, tick 27 GENBA]
severity: medium
---
# loop_state.md grew to ~198 KB and is re-Read IN FULL at the top of nearly every tick (recording muda)

**Pathology.** `loop_state.md` is the loop's only cross-tick memory, but it accumulates the full increment design brief for every sprint AND verbose GENBA/BUILD/REVIEW/HANSEI narration for all 27 ticks with no rotation or summarization. Verified live: the file is 198,670 bytes (936 lines). Multiple GENBA phases explicitly "Read state IN FULL" / "Read loop_state IN FULL" before each build — a re-read cost that grows linearly per tick (Muda/Muri). The load-bearing machine-read part is only the YAML frontmatter plus the latest HANSEI, yet every fresh-context tick pays to parse the entire history.

**Evidence (cited ticks).**
- tick 22 GENBA — "Read state IN FULL + config + the M1 plan IN FULL" (the whole monolith re-parsed before the ingest build).
- tick 23 GENBA — "Read loop_state IN FULL + config + the M1 plan IN FULL" again at the next tick.
- tick 27 GENBA — "Read loop_state IN FULL + config + M1 plan full" at the final M1 tick, when the file is at its largest.

**Proposed change.** In the autobuild-loop engine, add a bounded-memory discipline to the PHASE-6 close-out / state-schema (`~/.claude/skills/autobuild-loop/references/phases.md` §3.6 + `references/state-schema.md`): keep the YAML frontmatter + the most recent N ticks' decisions-log triples live in `loop_state.md`, and roll older completed-tick triples + consumed design briefs into an append-only archive (e.g. `.autobuild/loop_state_archive/`, or the kaizen ledger once it exists). GENBA's "Read state" then becomes O(recent) instead of O(all-history). The frontmatter (the only machine-read part) stays authoritative and small; the archive stays git-committed for audit.

**Does NOT weaken the immutable core because.** Rotation is additive bookkeeping over the engine's own memory file; it does not touch the seal, cost guard, plan-lock, no-auto-push, no-build-on-red, the no_progress counter, or the hash chain, and edits none of the three sealed files. The committed-state durability Poka-Yoke (commit-before-compaction) is preserved — archived triples are still committed, just not re-read in full each tick.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
