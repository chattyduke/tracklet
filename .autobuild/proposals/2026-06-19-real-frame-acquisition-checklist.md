---
status: applied  # 2026-06-20 — added [real_frame_acquisition] (four-property prerequisite checklist + structural-blocker note) to .autobuild/config.md; config gate PASSED (config.load_config dry-run validates); invariant-core SHA unchanged.
target: project-config
pathology_class: constituent-skill
key: real-frame-acquisition-checklist
date: 2026-06-19
cites: [tick 19 ANDON, tick 19 HANSEI, tick 20 ANDON]
severity: medium
---
# Real-frame sourcing burned two human-andon halts because the four required properties are split across disjoint corpora and nothing warned the planner

**Pathology.** Real-frame sourcing was structurally hard and the loop only discovered WHY by burning two consecutive human-andon halts. Datasets that publish FITS carry no externally-established NORAD identity, and papers that establish identity ship no retrievable FITS+WCS+UTC frame — the four required properties are split across two disjoint corpora. The same wall reappeared in the orbital-truth half: historical-by-date TLEs are gated behind credentialed Space-Track. Both were predictable acquisition prerequisites, but nothing in the config warned the planner, so the cost was paid as two no-merge ticks plus two human round-trips.

**Evidence (cited ticks).**
- tick 19 ANDON — the Sprint-1 frame gate fires after a full BUILD tick of web-searching NOIRLab/ZTF/SDSS/HST/Frigate/StreakMind: "FITS-publishers vs identity-publishers are disjoint corpora"; no_progress 0→1, human round-trip.
- tick 19 HANSEI — names the structural gap explicitly: "FITS + header WCS + precise UTC + externally-established NORAD identity, all four in one downloadable frame" is rare precisely because identity-correlation is hard work most publishers don't ship.
- tick 20 ANDON — with a frame in hand, the SAME wall in the orbital-truth half: "historical TLEs by date are gated behind Space-Track" (CelesTrak gp-history 404s for the public); a second halt, no_progress 0→1.

**Proposed change.** Add a real-frame acquisition checklist to the M1 (and any future real-data) milestone in `.autobuild/config.md`, naming the four properties that must co-occur in ONE downloadable frame BEFORE a real-image sprint starts: (a) retrievable FITS (byte-identical via SHA-pinned stream); (b) a pointing reference (header WCS OR a documented commanded-pointing + empirical camera offset); (c) precise UTC (DATE-OBS start + EXPTIME); (d) an EXTERNALLY-established NORAD identity (dataset-carried, not loop-correlated). Note the structural blocker (FITS-publishers vs identity-publishers are disjoint corpora) and that historical TLE-by-date requires a credentialed Space-Track pull. This makes frame+TLE acquisition an explicit human-gated prerequisite surfaced at PLAN time, not a mid-BUILD surprise that spends two andon ticks.

**Does NOT weaken the immutable core because.** It is documentation-only in project-config and REINFORCES, never relaxes, the non-circularity / no-correlator rail — it codifies that identity must be EXTERNAL, never loop-derived. It does not touch the cost guard, seal, plan-lock, no-auto-push, no-build-on-red, the no_progress counter, the hash chain, or any sealed file.

**Apply path.** A human flips status: proposed -> approved, then /autobuild-optimize --apply (skill changes gated by ablation; config changes by schema-valid dry-run).
