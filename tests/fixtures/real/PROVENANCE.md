# M1 real frame — provenance & sign-off

The single real, public satellite image the M1 pipeline runs on, and the externally-established
satellite identity it is scored against. Everything here is needed for a stranger to reproduce the
M1 residual from scratch.

## The frame

| Field | Value |
|---|---|
| Member | `BW3_DDOTI_data/20221118/20221118T024706C1o.fits.fz` |
| Instrument | DDOTI camera **C1** (28-cm f/2.2), OAN-SPM San Pedro Martir, Mexico |
| `DATE-OBS` (exposure **start**, UTC) | `2022-11-18T02:47:16.782` |
| `EXPTIME` | `10.0` s |
| `MJD-OBS` | `59901.11616647` |
| Detector | 6144 × 6220, BITPIX 16 (unsigned, BZERO 32768), single PRIMARY image HDU |
| Plate scale / FOV | ≈ 2.0″/px, ≈ 3.41° |
| **Header WCS** | **NONE** (0 WCS keywords — verified by reading the header). Pointing-truth is therefore the commanded mount pointing (`STRCURA`=303.6068°, `STRCUDE`=−16.2040°) + an empirically-derived fixed C1 offset (Sprint 4 / AC 4.6), **not** a header WCS. |

### Source (primary + mirror)

- **Primary:** Zenodo record **8102655** — DOI `10.5281/zenodo.8102655`, *"Raw FITS … BlueWalker 3"*, **CC-BY-4.0**.
  - Archive `BW3_DDOTI_data.tgz` (2,399,378,573 B) at
    `https://zenodo.org/api/records/8102655/files/BW3_DDOTI_data.tgz/content`.
- **Mirror:** `https://zenodo.org/record/8102655/files/BW3_DDOTI_data.tgz?download=1` (Zenodo legacy files path).
- **Member integrity:** size **17,507,520 B**, SHA-256
  `b6dcf797163fab78adca9316f0dcb18eb29e83c8c398ae325a292fad30519ca1`.

### Retrieval (stranger-reproducible — AC 1.1)

The `.fits.fz` / `.fits` are **gitignored** (`*.fits`); fetch on demand, never committed (a multi-MB binary in
non-LFS git history is one-way bloat).

```sh
tests/fixtures/real/fetch.sh            # → tests/fixtures/real/20221118T024706C1o.fits(.fz)
```

`fetch.sh` **streams** the 2.4 GB archive and extracts **only** the single 17.5 MB member (never landing the
2.4 GB on disk), verifies it against the pinned member SHA-256 above (fails loud on mismatch), then `funpack`s
the Rice-compressed `.fits.fz` to a plain FITS. Reproducibility survives URL rot via the two URLs; the
integrity guarantee is the pinned SHA-256, not the URL.

> **Verified this tick:** `fetch.sh`'s streaming recipe was run live — the extracted member is byte-exact
> (17,507,520 B, SHA-256 `b6dcf797…19ca1`).

## Satellite identity (externally established — AC 1.4)

- **NORAD id 53807 = BlueWalker 3** (intl designator **2022-111AL**).
- **Identity is EXTERNAL via the dataset**, not recovered by us: the FITS header carries `BLKNM='BW3'` and
  `VSTNM='BW3'`, and the Zenodo record title is *"… BlueWalker 3"*. We do **not** build a streak-vs-catalogue
  correlator (that is PHASE 2). Identity is carried from the dataset, not from an `OBJECT` keyword and not from
  a correlation we performed.

### TLE (satellite-truth source)

Committed at `tests/fixtures/real/bluewalker3_53807.tle` (validated by the project's own checksum-gated
`scene.parse_tle_text`).

```
BLUEWALKER 3
1 53807U 22111AL  22321.51776124  .00001408  00000+0  82536-4 0  9993
2 53807  53.2022 319.8514 0014272 124.6871 235.5472 15.18590617 10265
```

- **Epoch** `22321.51776124` = **2022-11-17T12:25:34.6 UTC** — **0.598 d before** the exposure midpoint
  (well inside the ±2-day LEO usability window; the current 2026 TLE was rejected — 3.5 yr away = SGP4 fiction).
- **Checksums valid** (L1 = 3, L2 = 5; both 69 chars). **Orbit sane:** i = 53.2022°, mean motion 15.18590617
  rev/day ≈ ~510 km LEO, consistent with BlueWalker 3.
- **Source:** a CelesTrak `active.txt` 6-hourly full-catalog dump (data origin CelesTrak / Space-Track), via a
  GitHub read-only mirror
  `https://raw.githubusercontent.com/vzlusat/vzlusat1-timepix-decoder/master/misc/tle/147.228.97.106/tle/active-2022-11-18-06-05-01.txt`
  (dump downloaded 2022-11-18 06:05 UTC; the file carries the verbatim `BLUEWALKER 3` name line above the 53807
  element set). The **filename timestamp is the download time**; the **authoritative epoch is the decoded
  `22321.51776124`**. (For a sub-0.1-day epoch the only path is an authenticated Space-Track GP_HISTORY query —
  not needed for M1; 0.598 d is well within the LEO usability window.)

### Honest residual caveat (carried into the Sprint-5 degradation report)

A ~0.6-day-old LEO TLE contributes real along-track propagation error to the residual → named under the report's
**timing / ephemeris uncertainty** source. The M1 residual is the honest real-frame number (AC-4.6
plausibility-gated, not a tight residual gate); it will partly reflect TLE age, which is expected and truthful —
**not a defect to hide or flatter.**

## Observatory site

OAN-SPM / DDOTI, San Pedro Martir, Baja California, Mexico = **+31.044333° N, −115.46375° W, 2830 m**
(31° 02′ 39.60″ N / 115° 27′ 49.50″ W). **CONFIRMED (Sprint 3, tick 23)** to the published OAN-SPM position
([airmass.org/observatories/spm](https://airmass.org/observatories/spm), corroborated by OAN-UNAM site listings);
DDOTI sits on the OAN-SPM site. **The FITS header does not record the site geodetic coords**, so this is the
published *observatory* position, not a per-pier survey — the residual uncertainty within the ~hundred-metre
OAN-SPM campus is <~25″ for the ~510 km BW3 LEO (overhead worst case), far below the dominant ~arcminute TLE-age
along-track term (0.598 d). LEO parallax makes the site material (a ~63 m error ⇒ up to ~25″ apparent shift vs
the 10″ gate), which is why the earlier placeholder (31.0442 / −115.4633 / 2790 m) was confirmed-to-source.
`meta.toml` now records `site_confirmed = true`.

## C1 camera offset — derived NON-CIRCULARLY (Sprint 4 / AC 4.6, tick 25)

The DDOTI frame carries **no header WCS**, so the AC-4.6 plausibility gate needs an independently-known
pointing center. The commanded mount pointing alone (`STRCURA`/`STRCUDE` = 303.6068° / −16.2040°) sits
**2.25° from where the C1 camera actually points** — a real, fixed camera-to-mount offset. That offset was
derived **without ever touching the target frame's own recovered-minus-commanded** (which would be circular
and would always pass the gate). Instead, **3 OTHER same-night C1 frames** were blind-solved and the mean
offset taken:

| Source frame (member) | Blind-recovered center (RA, Dec) | offset (recovered − commanded) |
|---|---|---|
| `BW3_DDOTI_data/20221118/20221118T024735C1o.fits.fz` | (305.5564, −14.9639) | (+1.9496, +1.2401) |
| `BW3_DDOTI_data/20221118/20221118T024757C1o.fits.fz` | (305.5563, −14.9638) | (+1.9495, +1.2402) |
| `BW3_DDOTI_data/20221118/20221118T024816C1o.fits.fz` | (305.5562, −14.9639) | (+1.9494, +1.2401) |

- **Mean offset:** `camera_offset_ra_deg = +1.94952`, `camera_offset_dec_deg = +1.24011` (committed to `meta.toml [pointing]`).
- **Scatter:** max great-circle separation of any frame's recovered center from the mean-offset center = **0.00011° (0.4″)** — far below the **~0.1° Andon threshold**; the camera offset is rock-stable across the night.
- **Expected C1 pointing center for the target frame** = commanded + offset = **(305.5563, −14.9639)**.
- **Non-circularity preserved:** the offset comes from the OTHER 3 frames; the target frame `024706` contributes nothing to it. The target frame's own blind-recovered center (305.5565, −14.9640) then overlaps the expected center to **0.0002°** — << the 1.705° half-field tolerance — so the gate confirms field overlap and the residual is a real, non-circular measurement.
- The 3 source frames are fetched (single-pass stream of the same Zenodo archive) into `tests/fixtures/real/offset_*.fits.fz`; they are **gitignored** (`*.fits.fz` / `*.fits`), like the target frame. Re-derive with `tests/fixtures/real/_derive_offset.py` (also gitignored — a scratch helper).

### The milestone residual (AC 4.1 / AC 6.1)

With the offset committed, `run.py --image … --meta …` on the locked frame produces the **M1 numeric residual
= 315.52″** (AC-4.6 plausibility gate PASSED: recovered field overlaps expected field, separation 0.0002° ≤
1.705°). This is the **honest real-frame number**, dominated by the documented **0.598-day TLE-age along-track
term** (BlueWalker-3 moves arcminutes per second; a ~0.6-day-old LEO TLE accumulates real along-track error of
this magnitude). It deliberately does **not** pass the M0 synthetic 10″ gate — the milestone DoD is a *reported*
residual passing the *plausibility* gate, not a tight residual. The five-source degradation decomposition that
attributes this 315.52″ across pointing/timing/site/plate-scale/noise is the **Sprint-5** report.

## Smoke verification (live, this tick — AC 1.2 / AC 1.3)

`solve_pointing` and `detect_streak` were run **verbatim** (reused from M0) on the **raw funpacked frame**.
solve-field solves **blind** by default even though no header WCS is present; the detector reads only the image.

| Check | Result |
|---|---|
| **AC 1.2** `solve_pointing(frame, {"fov_deg": 3.41})` | **`SolveResult`** in 8.4 s — recovered center (RA, Dec) = **(305.557°, −14.964°)** |
| **AC 1.3** `detect_streak(frame)` | **`StreakDetection`** in 3.4 s — midpoint px (4681.7, 3129.0), trail length ≈ 4956 px @ 126.16° |

Both returned **non-failure** types → the candidate genuinely blind-solves and detects. (This smoke is on the
**raw** frame; Sprint-2 **AC 2.5** is the binding confirmation that the **normalized / WCS-stripped** ingest
output still solves+detects. If AC 2.5 fails, this frame is rejected and selection returns to Sprint 1.)

## Human sign-off (AC 1.5)

**Frame + NORAD id + provenance CONFIRMED by Sam** at the Sprint-1 human andon gate
(`/autobuild-loop` tick 19 → 20): the BlueWalker-3 / DDOTI `20221118T024706C1o` frame (NORAD 53807,
Zenodo 8102655), the no-header-WCS pointing-truth adaptation (commanded `STRCURA`/`STRCUDE` + an empirically,
non-circularly derived fixed C1 offset), and the **strict AC-4.6** plausibility gate were all approved, with
Sprints 1→6 authorized to run autonomously frame-in-hand. The historical NORAD-53807 TLE dependency that briefly
re-raised the gate (tick 20) is resolved and independently re-verified above.

> **AC-1.5 status: CLEARED.** The Sprint-1 lock is **provisional** — Sprint-2 AC 2.5 (the normalized image still
> blind-solves + detects) is the binding confirmation.
