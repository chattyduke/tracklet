---
status: proposed
target: generic-skill
pathology_class: loop-itself
key: kaizen-ledger-never-appended-by-hansei
date: 2026-06-19
cites: [tick 2 HANSEI, tick 9 HANSEI, tick 11 HANSEI, tick 21 HANSEI, tick 27 HANSEI]
severity: high
---
# HANSEI never appends to kaizen_ledger.jsonl — the optimizer's substrate is empty by construction

**Pathology.** The engine designates a kaizen ledger as `/autobuild-optimize`'s input (invariant-core.md describes it as an append-only prev-hash chain; the optimize skill references an S4 APPEND path), but NO phase actually writes it. The HANSEI / PHASE-6 close-out writes ONLY `loop_state.md`. Across all 27 ticks the file was never created — verified live: `ls .autobuild/` shows `config.md`, `loop_state.md`, and an empty `proposals/`; there is no `kaizen_ledger.jsonl` anywhere under `.autobuild/`. Every Kaizen reflection landed in `loop_state.md` HANSEI prose, so a milestone-boundary optimizer run reads an absent ledger and has nothing mechanical to triage.

**Evidence (cited ticks).**
- tick 2 HANSEI — emits a full "KAIZEN for next tick" (reuse the certifi-CA + retry pattern in S1) into loop_state prose; no ledger append.
- tick 9 HANSEI — emits two numbered KAIZEN items (S6 SolveFailure-on-malformed-hint; render seal re-verify) into prose; no ledger append.
- tick 11 HANSEI — emits a KAIZEN (S5 read-side seal) into prose; no ledger append.
- tick 21 HANSEI — explicitly names a process gap ("every state mutation that changes the build's premise MUST carry its own decisions-log triple") as a standing Kaizen, recorded only in prose; no ledger append.
- tick 27 HANSEI — declares "/autobuild-optimize is now DUE" at the M1→M2 boundary while the ledger it would consume was never written.

**Proposed change.** In the autobuild-loop generic engine, add an explicit ledger-append step to the HANSEI / PHASE-6 close-out (edit `~/.claude/skills/autobuild-loop/references/phases.md` §3.6 and the HANSEI bullet; optionally clarify `references/state-schema.md` prose). After writing the per-tick HANSEI note into `loop_state.md`, the engine MUST append one structured entry to `<repo>/.autobuild/kaizen_ledger.jsonl` capturing: tick number, phase outcomes, what-worked, what-was-painful, the named Kaizen-for-next-tick, the merge-vs-bounce result, and the prev-hash so the append-only chain is actually formed. Keep the order inside the existing commit-before-compaction Poka-Yoke (write loop_state → append ledger → git commit both → only then compaction). Do NOT edit `ledger.py` (sealed) — wire the call site, not the sealed writer.

**Does NOT weaken the immutable core because.** It ADDS the missing writer and FORMS (does not remove) the prev-hash chain the invariant core already mandates. It touches only the generic engine's HANSEI/PHASE-6 spec, none of the three sealed files (invariant-core.md, optimize_scan.py, ledger.py). The commit-before-compaction Poka-Yoke and no-auto-push are respected (the append precedes the same per-tick commit; no push).

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
