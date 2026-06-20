#!/usr/bin/env python3
"""Build the static, zero-backend tracklet showcase page (M2 Sprint 5).

Reads the committed honest display snapshot ``showcase/data/m1_result.json`` and text-templates a
single static ``showcase/index.html``. The page serves NO backend, takes NO input, and recomputes
NOTHING — it is a frozen presentation of one real M1 run. Open it over ``file://`` with no server.

Seal Poka-Yoke (load-bearing): this generator lives in ``scripts/``, OUTSIDE ``src/tracklet/``, so it
may freely ``json.load`` its DISPLAY data without tripping the repo-wide
``json.load``-only-in-``score`` seal guard (which AST-scans only ``src/tracklet/*.py``). The display
data is a snapshot of a real M1 run — it is NOT the sealed ``truth.json`` and is NOT recomputed here.

Honest framing (NOT flattery): the page states the 315.52″ is the genuine real-frame number,
dominated by the 0.598-day-old TLE's along-track error, blind-solved with no position prior, and
explicitly NOT a synthetic-gate pass; the AC-4.6 plausibility center was derived non-circularly.

Idempotent: re-running overwrites ``showcase/index.html`` deterministically from the same data.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SHOWCASE = _REPO / "showcase"
_DATA_PATH = _SHOWCASE / "data" / "m1_result.json"
_OUT_PATH = _SHOWCASE / "index.html"
_OVERLAY = _SHOWCASE / "assets" / "m1_overlay.png"


def _esc(value: object) -> str:
    """HTML-escape a scalar for safe static interpolation."""
    return html.escape(str(value), quote=True)


def _load_display_data() -> dict:
    """Read the committed honest display snapshot. This is the page's ONLY data source — a fresh
    clone has no real frame to recompute from, so the committed snapshot is authoritative (its drift
    from the canonical PROVENANCE figures is gated by tests/test_showcase.py AC 5.2b)."""
    with _DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _render_sources(sources: list[dict]) -> str:
    rows = []
    for i, s in enumerate(sources, start=1):
        flag = ' <span class="dominant">DOMINANT</span>' if s.get("dominant") else ""
        rows.append(
            "      <li><strong>{i}. {name}</strong>{flag}<br>"
            "<span class=\"note\">{note}</span></li>".format(
                i=i, name=_esc(s["name"]), flag=flag, note=_esc(s["note"])
            )
        )
    return "\n".join(rows)


def _render_overlay() -> str:
    """If a committed overlay thumbnail exists, embed it; otherwise the page degrades to numbers-only.
    Referenced by a RELATIVE local path only (no network)."""
    if _OVERLAY.exists():
        return (
            '    <figure class="overlay">\n'
            '      <img src="assets/m1_overlay.png" alt="M1 result overlay (downsampled DDOTI frame)">\n'
            '      <figcaption>Downsampled overlay of the DDOTI frame &mdash; '
            "DDOTI / BlueWalker 3, Zenodo 8102655, CC-BY-4.0.</figcaption>\n"
            "    </figure>\n"
        )
    return (
        '    <p class="numbers-only">(No overlay thumbnail committed &mdash; numbers-only view. '
        "The source frame is not redistributed; see <code>showcase/NOTICE</code>.)</p>\n"
    )


def build() -> Path:
    """Render showcase/index.html from the committed display data. Returns the output path."""
    d = _load_display_data()

    residual = d["residual_arcsec"]
    residual_arcmin = d.get("residual_arcmin")
    threshold = d["residual_threshold_arcsec"]
    ra = d["recovered_center_ra_deg"]
    dec = d["recovered_center_dec_deg"]
    exp_ra = d["expected_center_ra_deg"]
    exp_dec = d["expected_center_dec_deg"]
    sep = d["plausibility_separation_deg"]
    tol = d["plausibility_tolerance_deg"]
    length = d["detect_length_px"]
    angle = d["detect_angle_deg"]
    tle_age = d["tle_age_days"]
    src = d["source"]

    sources_html = _render_sources(d["degradation_sources"])
    overlay_html = _render_overlay()

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tracklet &mdash; M1 real-image result</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: -apple-system, system-ui, "Segoe UI", sans-serif; max-width: 52rem;
           margin: 0 auto; padding: 2rem 1.25rem; line-height: 1.5; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
    .sub {{ color: #666; margin-top: 0; }}
    .residual {{ font-size: 2.4rem; font-weight: 700; margin: 0.5rem 0; }}
    .residual small {{ font-size: 1rem; font-weight: 400; color: #666; }}
    .honest {{ background: rgba(127,127,127,0.10); border-left: 4px solid #b38600;
              padding: 0.9rem 1.1rem; border-radius: 4px; margin: 1.2rem 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.75rem 0; }}
    th, td {{ text-align: left; padding: 0.35rem 0.6rem; border-bottom: 1px solid rgba(127,127,127,0.25); }}
    th {{ width: 40%; font-weight: 600; }}
    ul {{ padding-left: 1.1rem; }}
    li {{ margin-bottom: 0.6rem; }}
    .dominant {{ background: #b38600; color: #fff; font-size: 0.7rem; font-weight: 700;
                 padding: 0.1rem 0.4rem; border-radius: 3px; vertical-align: middle; }}
    .note {{ color: #666; font-size: 0.92rem; }}
    .overlay img {{ max-width: 100%; height: auto; border: 1px solid rgba(127,127,127,0.3); }}
    .numbers-only {{ color: #888; font-style: italic; }}
    footer {{ margin-top: 2rem; color: #888; font-size: 0.85rem; border-top: 1px solid rgba(127,127,127,0.25);
              padding-top: 0.9rem; }}
    code {{ font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>tracklet &mdash; M1 real-image result</h1>
  <p class="sub">A software-first optical Space-Domain-Awareness pipeline, run on ONE real,
     public telescope frame. Static page &mdash; no backend, no compute, no input. Precomputed once
     from a real run; this page recomputes nothing.</p>

  <div class="residual">{_esc(residual)}&Prime;
    <small>(&asymp; {_esc(residual_arcmin)}&prime;) &mdash; real on-sky residual</small></div>

  <div class="honest">
    <strong>Honest framing.</strong> {_esc(residual)}&Prime; is the genuine real-frame number &mdash;
    reported verbatim, never rounded to flatter. It is <strong>dominated by the TLE-age along-track</strong>
    error: the orbital element set is {_esc(tle_age)} days old, and BlueWalker&nbsp;3 moves arcminutes
    <em>per second</em> in low Earth orbit, so a sub-day-old TLE accrues real along-track slip of this
    scale. The frame was <strong>blind-solved with no position prior</strong>. This residual is
    <strong>NOT a synthetic-gate pass</strong> &mdash; it deliberately does <em>not</em> clear the
    {_esc(threshold)}&Prime; synthetic M0 gate; the M1 definition of done is an honest, plausibility-gated
    residual, not a tight one. The AC-4.6 plausibility center used to confirm the solver locked onto the
    right sky was derived <strong>non-circularly</strong> (from 3 <em>other</em> same-night frames, never
    the target frame's own recovered pointing).
  </div>

  <h2>What was measured</h2>
  <table>
    <tr><th>Satellite</th><td>{_esc(d['satellite_name'])} (NORAD {_esc(d['norad_id'])})</td></tr>
    <tr><th>Frame</th><td>DDOTI exposure, {_esc(d['exposure_start_utc'])} UTC, {_esc(d['exposure_s'])}&nbsp;s</td></tr>
    <tr><th>Detected trail</th><td>&asymp; {_esc(length)} px @ {_esc(angle)}&deg;</td></tr>
    <tr><th>Blind-recovered center</th><td>RA {_esc(ra)}&deg;, Dec {_esc(dec)}&deg;</td></tr>
    <tr><th>Expected center (non-circular)</th><td>RA {_esc(exp_ra)}&deg;, Dec {_esc(exp_dec)}&deg;</td></tr>
    <tr><th>Plausibility separation</th><td>{_esc(sep)}&deg; &le; {_esc(tol)}&deg; tolerance &rarr; field overlap CONFIRMED</td></tr>
    <tr><th>Plate solver</th><td>{_esc(d['plate_solver'])}</td></tr>
  </table>

{overlay_html}
  <h2>Where the residual comes from (largest first)</h2>
  <ul>
{sources_html}
  </ul>

  <footer>
    <p><strong>Source frame.</strong> {_esc(src['title'])} &mdash;
       Zenodo record {_esc(src['zenodo_record'])}, DOI {_esc(src['doi'])},
       licence <strong>{_esc(src['licence'])}</strong>. DDOTI / OAN-SPM, San Pedro Martir, Mexico.
       The frame is not redistributed here; only the precomputed numeric result is committed
       (<code>showcase/data/m1_result.json</code>). See <code>showcase/NOTICE</code>.</p>
    <p>tracklet code: MIT. This page is static &mdash; generated by
       <code>scripts/build_showcase.py</code>, opens over <code>file://</code> with no server.</p>
  </footer>
</body>
</html>
"""

    _OUT_PATH.write_text(page, encoding="utf-8")
    return _OUT_PATH


def main() -> int:
    out = build()
    print(f"wrote {out.relative_to(_REPO)} from {_DATA_PATH.relative_to(_REPO)} (static, zero-backend)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
