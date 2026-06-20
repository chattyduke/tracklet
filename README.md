# tracklet

<!-- CI badge — fill the real slug at the publish/push human gate (the repo is LOCAL until then):
[![CI](https://github.com/<OWNER>/tracklet/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/tracklet/actions/workflows/ci.yml)
The badge only goes live AFTER the first push triggers a real GitHub Actions run — see "CI & the publish/push human gate" below. Do NOT claim CI green before that run. -->

**An atomic proof of a software-first optical Space-Domain-Awareness (SDA) pipeline.**

`tracklet` takes a sky image, recovers where it is pointing (blind plate-solve), finds a
satellite streak in it, measures the satellite's position, and reports **how far that
measurement is from known truth — in arcseconds**.

The scene is **synthetic but built from REAL public data** (real Gaia DR3 stars + a real
satellite TLE), so truth is known *by construction*. The end-to-end golden test — render a
known scene → run the pipeline → assert `residual_arcsec < THRESHOLD` — **is** the executable
definition of done.

> **Status:** M1 complete (`v0.1.1`). M0 (`v0.1.0`) recovers the satellite to **2.08″** on the
> synthetic-from-real-data scene (gate 10″). **M1 runs the *exact same pipeline* on ONE real,
> public telescope frame** — a DDOTI image of BlueWalker 3 — and reports an **honest real residual
> of 315.5″**, blind-solved with no position prior and scored against an independently-sealed TLE
> truth. That residual is *deliberately not* a flattering number: it is dominated by a 0.6-day-old
> orbital element set (real along-track propagation error), and reporting it truthfully — rather
> than hiding or rounding it — is the entire point of M1. See **[Real image (M1)](#real-image-m1)**.
> The sealed-truth / non-circularity boundary is formally pinned by `tests/test_seal.py`.

## What this proves — and what it does NOT

- **Proves:** an end-to-end astrometric pipeline (plate-solve → detect → measure → score) can
  recover a satellite's sky position to a few arcseconds against independently-known truth, in a
  reproducible, offline, one-command run.
- **Does NOT prove:** that the pipeline is *accurate* on real hardware to arcseconds. M0 is a
  synthetic-from-real-data result, not a hardware measurement. M1 (below) runs the same pipeline on
  one real telescope frame and gets **315.5″** — honest, but coarse, and dominated by a stale TLE,
  not by the sensor. What M1 *does* prove is that the pipeline **runs unchanged on a real frame**
  (blind-solves it, detects the real streak, measures it, scores it) and **reports the real number
  truthfully** including a decomposition of where the degradation comes from. Tightening that
  residual (current TLE, header-WCS pointing-truth, per-frame timing) is future work, not a V0.1
  claim.

## Quickstart (stranger-reproducible)

```bash
git clone <repo> tracklet && cd tracklet
make setup                 # creates .venv (Python 3.14), installs tracklet (editable) + dev deps
#   — OR, the exact-reproduce pip path (no editable install):
#   python3.14 -m venv .venv && .venv/bin/pip install . -c requirements.lock
./scripts/install_indexes.sh   # one-time: installs solve-field + ~340 MB wide-field indexes
make test-golden           # the @solver golden e2e: render -> blind-solve -> residual < 10"
make run                   # the one command -> out/{residual.txt, overlay.png, report.md, track.tdm}
make test                  # fast unit suite (NO solver needed; proves the seal + WCS math)
```

The TLE + Gaia fixtures are **committed** under `data/`, so reproducing the result needs no
network: a fresh `git clone` → install → `./scripts/install_indexes.sh` → `make test-golden`
recovers the ~2.081″ residual on a clean machine. `make fetch` is **optional** — it only re-freezes the
fixtures from CelesTrak + Gaia (online) and is not needed to reproduce.

### Install as a package — the `tracklet` console command

`tracklet` is a real **pip-installable** package (single-sourced version `0.1.2`). Installing it
exposes a `tracklet` **console command** (and a `python -m tracklet` module entry point), both of
which reuse `run.main` verbatim — same pipeline, same flags:

```bash
pip install . -c requirements.lock   # constraints file = exact-reproduce lock
tracklet --out out                   # the console script: synthetic scene -> out/{..., track.tdm}
python -m tracklet --out out          # identical module entry point
python -c "import importlib.metadata as m; print(m.version('tracklet'))"   # -> 0.1.2
```

> **`TRACKLET_DATA` for a manual stranger run.** A non-editable install lands `tracklet` in
> `site-packages`, where the `__file__`-relative `data/` (the committed Gaia/TLE fixtures) does **not**
> exist. For a manual install-then-run, point the CLI at the clone's fixtures:
> `TRACKLET_DATA="$PWD/data" tracklet --out out`. The editable `make setup` install resolves `data/`
> from the repo tree, so it needs no override; the clean-room script (below) sets `TRACKLET_DATA`
> automatically.

### Build a wheel + sdist

```bash
make build      # python -m build --no-isolation -> dist/tracklet-0.1.2-*.whl + .tar.gz
```

`make build` builds **offline** (`--no-isolation` reuses the dev-extra build backend, a Poka-Yoke
against PyPI build-isolation on a clean machine). Run `make setup` first so `build`/`setuptools`/
`wheel` are present in the venv. Artifacts land in `dist/` (gitignored — never committed).

### Autonomous clean-room reproduce

`make clean-room` (or `bash scripts/clean_room_reproduce.sh`) is the **autonomous clean-machine
proof** of the `pip`-installable package. It runs end-to-end with no manual steps:

```bash
make clean-room
```

It creates a **fresh temp dir**, `git clone`s the **committed HEAD** of this repo, builds a **fresh
`python3.14` venv** (never your dev `.venv`), does a **non-editable** `pip install . -c
requirements.lock`, then runs the **installed** `tracklet` CLI on the synthetic scene and asserts the
residual is **< 10″** (the real number is echoed) — and finally runs `pytest -m "not solver"` from the
**installed package** (not the source tree). The temp dir is torn down on exit; it reuses the host's
`solve-field` + wired indexes read-only and **never pushes**. If `solve-field` or the indexes are
missing it prints a loud remediation and exits non-zero (it tests the *package install + reproduce*,
not the solver install — install those first via `brew install astrometry-net` /
`apt-get install astrometry.net` + `./scripts/install_indexes.sh`). Because it clones the committed
HEAD, run it on a **clean tree** — uncommitted work is invisible to it by design.

> **Why `TRACKLET_DATA`:** a non-editable wheel lands `tracklet` in `site-packages`, where the
> `__file__`-relative `data/` (the committed Gaia/TLE fixtures) does not exist. The clean-room exports
> `TRACKLET_DATA="$CLONE/data"` so the installed CLI (and the installed-package pytest run) find the
> clone's committed fixtures. A stranger installing the wheel sets the same env var (documented in
> *On-disk footprint*); the editable dev install resolves `data/` from the repo tree as before.

## CCSDS TDM output (`track.tdm`)

On every **successful** run (synthetic **and** real), tracklet writes a **CCSDS Tracking Data
Message** (`out/track.tdm`, or `out_real/track.tdm` for the M1 real-frame path) alongside
`residual.txt`/`report.md`. It is a standard **TDM 503.0-B-2 RADEC** angles file — the
machine-readable form of the same measured track:

```text
CCSDS_TDM_VERS = 2.0
META_START
  TIME_SYSTEM       = UTC
  PARTICIPANT_1     = TRACKLET-SYNTH      # the real path uses the observatory name from meta.toml
  MODE              = SEQUENTIAL
  ANGLE_TYPE        = RADEC
  REF_FRAME         = EME2000
META_STOP
DATA_START
  <epoch> ANGLE_1 = <ra_deg>             # epoch = the exposure-MIDPOINT instant (the scored instant)
  <epoch> ANGLE_2 = <dec_deg>
DATA_STOP
```

The RA/Dec are `result.measured` verbatim; the epoch is the exposure **midpoint** (the same instant
`score` is taken at). The writer (`src/tracklet/tdm.py`) is a pure downstream-of-`score` text
formatter — it receives its inputs **in-memory** and contains **no `json.load`**, so it adds no
reader of the sealed truth (the seal stays intact). On a typed failure (solve/detect/wrong-field,
exits 2/3/4) **no `track.tdm` is written** — no fabricated track, exactly as `residual.txt` is
withheld.

## Real image (M1)

M1 takes the **exact M0 pipeline — unchanged** — and runs it on **one real, public telescope frame**
instead of a synthetic scene. No solving code changed: `solve_pointing` / `detect_streak` /
`measure_position` / `score` are reused verbatim; only a new **`ingest`** front-end (real FITS →
normalized, WCS-stripped clean image + a sealed `truth.json`) and a `run.py --image/--meta` branch
were added. The seal is unchanged — `score` is still the sole truth reader (`json.load` lives only in
`score.py`); the solver still receives a **WCS-free** image and **no** position prior.

**The frame.** A 10-second DDOTI exposure of **BlueWalker 3** (NORAD **53807**), taken
2022-11-18 02:47 UTC from OAN-SPM, San Pedro Martir, Mexico. It is public, **CC-BY-4.0**, on Zenodo
record [8102655](https://doi.org/10.5281/zenodo.8102655). The satellite's identity is **externally
established** (the dataset is published as a BlueWalker-3 observation; the FITS header tags it `BW3`)
— tracklet does **not** recover identity by correlation (that is a future phase). Full provenance,
the committed TLE, and the human sign-off are in
[`tests/fixtures/real/PROVENANCE.md`](tests/fixtures/real/PROVENANCE.md).

**The honest result: `residual_arcsec = 315.5″`.** The frame was blind-solved with **no** position
prior, the real satellite trail was detected (≈ 4956 px @ 126.16°), measured against the
blind-recovered WCS, and scored against the TLE-propagated truth. 315.5″ is **not** a defect and
**not** rounded to flatter — it is the genuine real-frame number, and a five-source degradation
report (emitted alongside it in `out_real/report.md`) attributes it: the **dominant** term is the
**0.598-day-old TLE** (BlueWalker 3 moves arcminutes *per second* in LEO, so a sub-day-old element
set carries real along-track error of this scale), with seeing/atmosphere, real optics/PSF, plate
scale, and detector noise as the smaller terms. The in-memory pointing-vs-timing split is
dRA −148.4″ / dDec −278.4″ (primarily along-track), consistent with a timing/ephemeris-dominated
residual rather than a pointing error.

**Why this is a real measurement, not a rigged one.** The DDOTI frame carries **no header WCS**, so
the plausibility gate (AC-4.6) needs an independently-known pointing center. That center was derived
**non-circularly** — by blind-solving **3 *other* same-night C1 frames** for the fixed camera-to-mount
offset, never the target frame's own recovered pointing (which would be circular and would always
pass). The target frame's blind-recovered field then overlaps the expected field to **0.0002°**
(≪ the 1.705° half-field tolerance), so the gate confirms the solver locked onto the *right* sky — a
wrong-asterism lock would have been reported as an honest typed failure, not a residual.

### Reproduce the M1 residual from scratch

```bash
# 0. Prereqs: M0 quickstart done (make setup + ./scripts/install_indexes.sh — same solver).
# 1. Fetch the real frame (streams a 2.4 GB Zenodo archive, extracts ONLY the 17.5 MB member,
#    verifies a pinned SHA256, funpacks to plain FITS). The .fits is gitignored — never committed.
tests/fixtures/real/fetch.sh
#    -> tests/fixtures/real/20221118T024706C1o.fits

# 2. Run the SAME pipeline on the real frame (the committed TLE is satellite-truth):
.venv/bin/python -m tracklet.run \
    --image tests/fixtures/real/20221118T024706C1o.fits \
    --meta  tests/fixtures/real/meta.toml \
    --out   out_real

# 3. Inspect the honest result:
cat out_real/residual.txt    # -> 315.52...  (the real arcsec residual)
cat out_real/report.md       # -> the five-source degradation report + pointing-vs-timing split
cat out_real/track.tdm       # -> the CCSDS TDM RADEC track for this frame
```

Expect a residual of **≈ 315.5″** and a report naming all five degradation sources with the
TLE-age along-track term flagged dominant. (The `@solver` test
`tests/test_real_image_e2e.py::test_ac41_real_image_run_produces_numeric_residual_passing_plausibility`
asserts exactly this end-to-end; it auto-skips if the frame has not been fetched.)

> **Honest-degradation, by design.** M1's residual deliberately does **not** pass M0's tight 10″
> synthetic gate — the M1 definition of done is a *reported* residual that passes the *plausibility*
> (right-field) gate, not a tight one. Learning the real failure modes on one frame — and reporting
> the real number — is the whole milestone. A current TLE would shrink the dominant term
> substantially; that is future work, not part of the V0.1.1 claim.

### Showcase page (static, zero-backend)

A single static page presents the precomputed M1 result — no server, no compute, no input:

```bash
make showcase                  # scripts/build_showcase.py -> showcase/index.html
open showcase/index.html       # opens over file:// — no server needed
```

[`showcase/index.html`](showcase/index.html) is generated from the committed honest snapshot
[`showcase/data/m1_result.json`](showcase/data/m1_result.json) (a frozen real-run result, **not** the
sealed `truth.json`, and **not** recomputed by the page). The figures on the page are anchored to
`tests/fixtures/real/PROVENANCE.md` by a numeric anti-drift test, so the snapshot can never silently
diverge from the real run. The generator lives in `scripts/` (outside `src/`) deliberately, so it can
deserialize its display data without touching the sealed-truth seal. The page states the honest 315.5″
verbatim, flags the TLE-age along-track term as dominant, and attributes the source DDOTI / BlueWalker-3
frame (Zenodo [8102655](https://doi.org/10.5281/zenodo.8102655), **CC-BY-4.0**); see
[`showcase/NOTICE`](showcase/NOTICE).

## CI & the publish/push human gate

A GitHub Actions workflow is **authored and committed** at
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) and **statically validated locally** (valid
YAML + `tests/test_ci_workflow.py` asserts its two jobs, the Python-3.14 pin, the lockfile install,
and the residual gate; no push/deploy/secret step). It declares two jobs on `ubuntu-latest`:

- **`unit`** — `pip install . -c requirements.lock` (+ dev), `pytest -m "not solver"`: the
  deterministic seal + WCS-convention + unit proof, cross-arch.
- **`golden-solver`** — installs `solve-field` (apt `astrometry.net`, with a version-floor
  assertion), wires + caches the ~340 MB indexes via the cross-platform `install_indexes.sh`, runs
  `pytest -m solver`, and **fails if the golden residual ≥ 10″** (the reproduce-the-residual gate).

> **Honest gate — read this.** `v0.1.x` is **LOCAL-only**; this repo has **no remote** until a human
> decides to publish. **x86_64-Linux CI greenness is confirmed by the GitHub Actions run that fires
> AFTER the human-gated push — it is NOT claimed green before that run.** Locally, the autonomous
> clean-room (above) proves the clone→install→reproduce **recipe** on *this* architecture; the
> **cross-architecture** proof is the human-gated Actions run, never faked. Pushing the repo, watching
> Actions go green on a clean x86_64-Linux runner, and applying the `v0.1.2` tag are a **terminal
> human gate** — the build loop **never auto-pushes** and never auto-creates the public repo. The CI
> badge (commented at the top of this file) goes live only after that first real run; fill the
> `[project.urls]` repo URL in `pyproject.toml` and the badge slug at the same publish step.

## Environment

- **Python 3.14** (validated env; exact patch pinned in `requirements.lock`). A runtime assertion
  fails loud on a wrong minor — recreate the venv with `make setup`.
- **Plate solver:** [astrometry.net](https://astrometry.net) `solve-field` + the wide-field
  4100-series index files (~340 MB). [ASTAP](https://www.hnsky.org/astap.htm) is the documented
  fallback if the astrometry.net mirrors are unreachable.

## On-disk footprint & uninstall

`tracklet` itself lives in this repo. Out-of-repo state created by the plate-solver gate:
`brew install astrometry-net` (Linux: `apt-get install astrometry.net`), the ~340 MB index download,
and an additive `add_path` line in `astrometry.cfg`. To remove: `brew uninstall astrometry-net`,
`rm -rf <index dir>`, and revert the `add_path` line.

Build/run artifacts stay inside the repo and are all gitignored: `.venv/`, `out/` (incl.
`track.tdm`), `out_real/`, `indexes/`, and the wheel/sdist output `dist/` + `build/` (run
`make clean` to remove `out/*` + `dist/` + `build/`). The 76 MB real M1 frame and the ~340 MB indexes
are **never committed** — they are gitignored and fetched on demand (footprint discipline). To drop a
pip-installed copy entirely: `pip uninstall tracklet`.

## Data provenance & licences

- **Stars (M0):** Gaia DR3 (ESA/Gaia/DPAC) — open data.
- **Orbit (M0):** ISS TLE from [CelesTrak](https://celestrak.org) — public.
- **Real frame (M1):** DDOTI / BlueWalker-3 FITS, Zenodo record
  [8102655](https://doi.org/10.5281/zenodo.8102655) — **CC-BY-4.0**. Fetched on demand by
  `tests/fixtures/real/fetch.sh` (gitignored), not redistributed here.
- **Real orbit (M1):** BlueWalker 3 (NORAD 53807) TLE, epoch 2022-11-17 — data origin
  CelesTrak / Space-Track; committed at `tests/fixtures/real/bluewalker3_53807.tle`. See
  `PROVENANCE.md` for the exact retrieval path.
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
