---
status: proposed
target: generic-skill
pathology_class: loop-itself
key: kaizen-ledger-one-time-backfill
date: 2026-06-19
cites: [tick 22 HANSEI, tick 26 HANSEI, tick 4 HANSEI, tick 25 HANSEI, tick 27 HANSEI]
severity: high
---
# One-time backfill of the 27-tick decisions-log Kaizen prose into kaizen_ledger.jsonl

**Pathology.** Because the ledger was never written (see kaizen-ledger-never-appended-by-hansei), all process-feedback for the entire M0+M1 run is trapped as free prose inside `loop_state.md` HANSEI notes. Genuinely recurring, optimizer-actionable signals are buried there and were re-discovered by hand rather than detected mechanically — most starkly the `json.load` substring-seal false-positive, which tick 26 HANSEI itself dates to "the THIRD time (ticks 22, 23, now 26)". A milestone-boundary `/autobuild-optimize` run (which tick 27 HANSEI declares DUE) has zero structured substrate to catch these recurrences.

**Evidence (cited ticks).**
- tick 22 HANSEI — first explicit record that a `json.load` literal tripped the coarse substring seal tests (names ticks 22/23); pure prose.
- tick 26 HANSEI — names the SAME defect "for the THIRD time (ticks 22, 23, now 26)" and proposes migrating the substring tests to an AST predicate — a recurrence only visible by reading three separate HANSEI prose blocks, not a query.
- tick 4 HANSEI — Gaia SSL + flakiness lesson recorded as prose KAIZEN, re-applicable downstream.
- tick 25 HANSEI — the parallel→serial→single-pass fetch lesson, explicitly noting the tick-24 KAIZEN ("fetch serially") was itself incomplete and re-learned this tick.
- tick 27 HANSEI — declares the milestone-boundary optimizer DUE, with no corpus for it to scan.

**Proposed change.** Add a one-time backfill utility/recipe to the autobuild-loop engine references (e.g. `~/.claude/skills/autobuild-loop/references/`) that parses the existing `loop_state.md` decisions-log HANSEI triples (ticks 1-27) and emits one append-only `kaizen_ledger.jsonl` entry per tick — tick number, phase, what-worked / what-was-painful / Kaizen-for-next-tick, merge-vs-bounce outcome — building the prev-hash chain forward from a genesis entry. The backfill is read-only over `loop_state.md` and write-only to the new ledger; it changes no source, no config, runs no git. It gives the now-DUE M1→M2 optimizer a real corpus so recurring waste (the 3x substring-seal false-positive, the spawn-tool-unavailable env note since tick 21, the fetch parallel→serial lesson) becomes mechanically detectable.

**Does NOT weaken the immutable core because.** Backfill is purely additive and read-only over `loop_state.md`; it constructs the hash chain (strengthening, not weakening, the chain invariant) and touches none of the three sealed files. No rail is affected — no push, no auto-handoff, no seal change, no plan-lock change.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
