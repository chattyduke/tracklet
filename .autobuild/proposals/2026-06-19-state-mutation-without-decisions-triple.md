---
status: proposed
target: generic-skill
pathology_class: loop-itself
key: state-mutation-without-decisions-triple
date: 2026-06-19
cites: [tick 19 ANDON, tick 20 ANDON, tick 21 GENBA, tick 21 HANSEI]
severity: medium
---
# A premise-bearing state mutation can be committed with NO decisions-log triple, breaking the fresh-context audit trail

**Pathology.** `loop_state.md` is the loop's only cross-tick memory, yet its build PREMISE can be changed — frontmatter fields and anti-spin/gate controls flipped — and committed with no accompanying decisions-log ReAct triple. A prior turn mutated the frontmatter (TLE marked RESOLVED, the human gate cleared) and committed it via 381810b without a triple. The next fresh-context tick could not trust the narrative and had to reconstruct and independently re-verify the claim (checksum, epoch decode, orbit sanity) from scratch before building on it. The discipline is named in the log but not ENFORCED by the engine spec, so a fresh-context tick cannot rely on the log being complete.

**Evidence (cited ticks).**
- tick 19 ANDON — raises `human_gate=true` and sets `no_progress_count 0→1` as the frame-acquisition gate fires; gate/counter control fields mutated.
- tick 20 ANDON — raises the gate again and increments the counter for the TLE blocker; same control fields mutated at a resumption boundary.
- tick 21 GENBA — states plainly: "the committed state claim[ed] the TLE blocker RESOLVED — but the decisions log had NO tick recording that resolution (the TLE-resolved frontmatter rode in via commit 381810b without a ReAct triple)", forcing a from-scratch re-derivation of checksum/epoch/orbit.
- tick 21 HANSEI — names it exactly: "a prior turn mutated the state frontmatter (TLE resolved, counters reset) and committed it WITHOUT an accompanying decisions-log ReAct triple — a half-recorded panel."

**Proposed change.** In the autobuild-loop engine's PHASE-6 close-out (`~/.claude/skills/autobuild-loop/references/phases.md` §3.6) and the §3.5 GENBA gates, make the standing discipline a checked Poka-Yoke: any commit that mutates a premise-bearing frontmatter field (plan_sha256/plan_file, last_green_sha, no_progress_count, human_gate, status, or an open_findings resolution) MUST be accompanied in the SAME commit by a decisions-log triple recording the cause (e.g. "human cleared the frame gate", "TLE supplied by Sam — verified genuine"). Add a §3.5 GENBA check: if the incoming state shows such a field flipped since the last triple's recorded value with NO triple explaining it, treat it as an unverified premise and re-derive before building (codifying what tick 21 did by good instinct, so it is mechanical not heroic).

**Does NOT weaken the immutable core because.** It strengthens recording integrity and tightens (does not loosen) what the loop trusts before building, complementing no-build-on-red and the §3.5 gates. It requires a recorded justification for every flip of the very fields the core depends on — it never changes the no_progress increment logic, the gate threshold, or any tolerance. It touches only the engine's GENBA-gate / PHASE-6 spec, none of the three sealed files.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
