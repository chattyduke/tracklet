---
status: proposed
target: project-config
pathology_class: constituent-skill
key: large-artifact-stream-extract-pokayoke
date: 2026-06-19
cites: [tick 22 HANSEI, tick 24 HANSEI, tick 25 BUILD]
severity: medium
---
# Large-artifact acquisition friction (whole-archive download, parallel stalls) was re-discovered and hand-fixed every tick

**Pathology.** Sourcing real-frame data from a multi-GB Zenodo archive caused repeated, uncodified fetch friction. The 2.4 GB archive blew the 600s curl window mid-download; 3-way parallel range-reads stalled at 0 bytes; per-frame serial re-seeks wasted ~25 min each. The fix that actually works — stream + extract only the single needed member (~17.5 MB), verify a pinned member SHA256, never pull the whole archive to disk, and pay any deep-archive seek ONCE via a single-pass multi-member extraction — was invented ad-hoc and lives only in `tests/fixtures/real/fetch.sh`, NOT in the engine or config, so a future milestone/project re-learns it from scratch.

**Evidence (cited ticks).**
- tick 22 HANSEI — "the 2.4 GB Zenodo archive exceeded the 600s curl window on both urls (160/2400 MB)", forcing the binding AC 2.5 to SKIP.
- tick 24 HANSEI — single-stream fetch.sh works (~3 min, server-side seek dominates; "the member is only 17.5 MB"); 3-way parallel stalled (0 bytes in 8 min).
- tick 25 BUILD — "3-way parallel + per-frame serial both too slow/stalled → SINGLE-PASS one-stream extraction of all 3 members in archive order [deep 2.4 GB seek paid ONCE, ~30 min]"; the recipe folded into `fetch.sh --offset-frames`.

**Proposed change.** Add an `[acquisition]` block to `.autobuild/config.md` documenting the durable rule the loop paid three ticks to learn: when sourcing data from a large remote archive, NEVER download the whole archive to disk — stream and extract only the needed member(s) (`tar -xzO` / range-read), pin and verify a per-member SHA256, and pay any deep-archive seek ONCE via a single-pass multi-member extraction (not parallel, not per-member serial). State an explicit member-size expectation (here ~17.5 MB) and that whole-archive size (2.4 GB) must never hit the working tree. The BUILD phase reads this as a fetch Poka-Yoke so a future milestone inherits stream-extract-and-verify by default.

**Does NOT weaken the immutable core because.** It is purely additive acquisition guidance in project-config and touches no rail. It STRENGTHENS the SHA-pin / byte-identical-reproduce discipline and never edits invariant-core.md, optimize_scan.py, or ledger.py. It does not affect the seal, non-circularity, plan-lock, no-auto-push, no-build-on-red, the no_progress counter, or the hash chain.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
