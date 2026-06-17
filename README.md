# tracklet

**An atomic proof of a software-first optical Space-Domain-Awareness (SDA) pipeline.**

`tracklet` takes a sky image, recovers where it is pointing (blind plate-solve), finds a
satellite streak in it, measures the satellite's position, and reports **how far that
measurement is from known truth — in arcseconds**.

The scene is **synthetic but built from REAL public data** (real Gaia DR3 stars + a real
satellite TLE), so truth is known *by construction*. The end-to-end golden test — render a
known scene → run the pipeline → assert `residual_arcsec < THRESHOLD` — **is** the executable
definition of done.

> **Status:** under construction. Sprint 0 (environment + plate-solver gate) is the current
> milestone. The pipeline modules (S1–S7) are stubs until their sprints land.

## What this proves — and what it does NOT

- **Proves:** an end-to-end astrometric pipeline (plate-solve → detect → measure → score) can
  recover a satellite's sky position to a few arcseconds against independently-known truth, in a
  reproducible, offline, one-command run.
- **Does NOT prove:** anything about a real optical sensor. This is a synthetic-from-real-data
  result, not a hardware measurement. Real sensor noise, timing offsets, and atmospheric effects
  are out of scope for V0.1 (the V0.1.1 stretch runs the same pipeline on one real image).

## Quickstart (stranger-reproducible)

```bash
git clone <repo> tracklet && cd tracklet
make setup                 # creates .venv (Python 3.14), installs deps
./scripts/install_indexes.sh   # one-time: installs solve-field + ~340 MB wide-field indexes
make fetch                 # one-time: freezes the TLE + Gaia cone fixtures (online)
make run                   # the one command -> out/{residual.txt, overlay.png, report.md}
make test                  # unit suite (no solver needed)
make test-golden           # the @solver golden e2e (needs the plate-solver gate above)
```

## Environment

- **Python 3.14** (validated env; exact patch pinned in `requirements.lock`). A runtime assertion
  fails loud on a wrong minor — recreate the venv with `make setup`.
- **Plate solver:** [astrometry.net](https://astrometry.net) `solve-field` + the wide-field
  4100-series index files (~340 MB). [ASTAP](https://www.hnsky.org/astap.htm) is the documented
  fallback if the astrometry.net mirrors are unreachable.

## On-disk footprint & uninstall

`tracklet` itself lives in this repo. Out-of-repo state created by the plate-solver gate:
`brew install astrometry-net`, the ~340 MB index download, and an additive `add_path` line in
`astrometry.cfg`. To remove: `brew uninstall astrometry-net`, `rm -rf <index dir>`, and revert the
`add_path` line. `.venv/`, `out/`, and `indexes/` are gitignored.

## Data provenance & licences

- **Stars:** Gaia DR3 (ESA/Gaia/DPAC) — open data.
- **Orbit:** ISS TLE from [CelesTrak](https://celestrak.org) — public.
- **Indexes:** astrometry.net 4100/4200-series — fetched at setup, not redistributed here.
- **Code:** MIT (see `LICENSE`).

## Error budget

Documented with the golden test in S7. Expected residual ~2–4″ (transverse centroid ⊕ solver WCS
RMS ⊕ TAN-projection discretization); gate `RESIDUAL_THRESHOLD_ARCSEC = 10″`, stretch target <5″.
The actual measured residual is always reported, pass or fail.
