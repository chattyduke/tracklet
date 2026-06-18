# tracklet

**An atomic proof of a software-first optical Space-Domain-Awareness (SDA) pipeline.**

`tracklet` takes a sky image, recovers where it is pointing (blind plate-solve), finds a
satellite streak in it, measures the satellite's position, and reports **how far that
measurement is from known truth — in arcseconds**.

The scene is **synthetic but built from REAL public data** (real Gaia DR3 stars + a real
satellite TLE), so truth is known *by construction*. The end-to-end golden test — render a
known scene → run the pipeline → assert `residual_arcsec < THRESHOLD` — **is** the executable
definition of done.

> **Status:** M0 complete (`v0.1.0`). The full pipeline runs end to end on the synthetic
> scene; the golden e2e recovers the satellite to **2.08″** against sealed truth (gate 10″).
> The sealed-truth / non-circularity boundary is formally pinned by `tests/test_seal.py`.

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
make test-golden           # the @solver golden e2e: render -> blind-solve -> residual < 10"
make run                   # the one command -> out/{residual.txt, overlay.png, report.md}
make test                  # fast unit suite (NO solver needed; proves the seal + WCS math)
```

The TLE + Gaia fixtures are **committed** under `data/`, so reproducing the result needs no
network: a fresh `git clone` → `make setup` → `./scripts/install_indexes.sh` → `make test-golden`
recovers the ~2″ residual on a clean machine. `make fetch` is **optional** — it only re-freezes the
fixtures from CelesTrak + Gaia (online) and is not needed to reproduce.

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

Expected residual **~2–4″** in quadrature: transverse streak-centroid ~2″ ⊕ solve-field internal
WCS RMS ~1–2″ ⊕ TAN-projection / pixel-scale discretization <1″. Gate
`RESIDUAL_THRESHOLD_ARCSEC = 10″` (a ~2–3× margin so a stranger's independent blind solve cannot
flake), stretch target <5″. The **observed** golden-e2e residual is **2.08″**. The actual measured
residual is always reported by `make run` and `make test-golden`, pass or fail.

The pixel convention (CD-sign / Y-flip / 0-vs-1 origin) is pinned **independently** of the solver by
deterministic sub-pixel WCS round-trip tests under `pytest -m "not solver"`, so a 1-px convention
regression — which would land ~7″, still under the 10″ gate — is caught hard upstream and cannot
hide under the golden gate.
