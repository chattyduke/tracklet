"""realtruth — assemble the SEALED satellite-truth for a real frame (M1 Sprint 3).

The real-frame counterpart to render's truth half. ingest (Sprint 2) produces the WCS-stripped
solver image; this module produces the `truth.json` the M0 `score` reads UNCHANGED:

    real FITS header (DATE-OBS, EXPTIME)  ->  exposure MIDPOINT (UTC)
    committed TLE  --propagate_satellite_radec(topocentric site)-->  ICRS RA/Dec at the midpoint
    -> truth.json{"scored_truth": {ra_deg, dec_deg}, ...}   (read ONLY by score._load_truth)

Seal discipline (why this module is sealed-compatible):
  * It WRITES truth.json with ``json.dump`` only — it NEVER deserializes truth. ``score`` remains the
    SOLE truth reader (the repo-wide alias-resistant seal test guards that the json-deserialize
    attribute calls appear only in score.py). This module deliberately never names that read token.
  * The satellite-truth propagation reuses render's pure ``propagate_satellite_radec`` (no
    reimplementation) so real and synthetic truth share the IDENTICAL ICRS astrometric frame.
  * The header WCS (pointing-truth, when a frame carries one) + the midpoint are returned IN-MEMORY
    on the result — the report's degradation diagnostic reads them downstream; they are NEVER written
    into the solver's image.fits and NEVER fed into the blind solve.

Timing semantics (AC 3.1, load-bearing): ``DATE-OBS`` is the exposure START on the UTC scale (DDOTI
convention; pinned in meta.toml). The scored instant is ``start + EXPTIME/2``. A 1 s timing error is
~arcminutes of LEO along-track motion — so the parse is strict and fails LOUD on ambiguity rather
than guessing.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path


def exposure_midpoint_utc(date_obs: str, exptime_s: float) -> dt.datetime:
    """Exposure MIDPOINT as a tz-aware UTC datetime: ``DATE-OBS(start) + EXPTIME/2``.

    ``date_obs`` is the exposure START on the UTC scale (DDOTI convention). Parsed robustly: ISO
    8601 with or without the ``T`` separator and with or without fractional seconds; a naive value
    (no tz suffix) is interpreted as UTC; an explicit tz offset is honored then normalized to UTC.
    Fails LOUD (``ValueError``) on an unparseable timestamp or a non-positive exposure — guessing a
    timing convention would silently corrupt the LEO satellite-truth by arcminutes.
    """
    if not isinstance(exptime_s, (int, float)) or exptime_s <= 0.0:
        raise ValueError(f"EXPTIME must be a positive number of seconds; got {exptime_s!r}")

    raw = str(date_obs).strip()
    # Normalize a trailing 'Z' (Zulu/UTC) to an explicit offset datetime.fromisoformat understands;
    # accept both 'T' and space separators (datetime.fromisoformat handles both on 3.11+).
    candidate = raw.replace("Z", "+00:00")
    try:
        start = dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"DATE-OBS {date_obs!r} is not a parseable ISO-8601 UTC timestamp; "
            "refusing to guess the timing convention (a 1 s LEO error ~= arcminutes)"
        ) from exc

    # Naive (no tz) -> the DDOTI convention is UTC; tz-aware -> normalize to UTC.
    start = start.replace(tzinfo=dt.timezone.utc) if start.tzinfo is None else start.astimezone(
        dt.timezone.utc
    )
    return start + dt.timedelta(seconds=float(exptime_s) / 2.0)


@dataclass(frozen=True)
class RealTruthResult:
    """Outcome of assembling the sealed real-frame satellite-truth.

    Attributes
    ----------
    truth_path : Path
        The written ``truth.json`` (read ONLY by ``score._load_truth``).
    scored_truth_ra_deg, scored_truth_dec_deg : float
        The satellite's ICRS RA/Dec (deg) at the exposure midpoint — the scored truth point.
    exposure_mid_utc : datetime.datetime
        The exposure midpoint (tz-aware UTC); returned in-memory for the report diagnostic.
    pointing_wcs : astropy.wcs.WCS | None
        The frame's header WCS (independent pointing-truth) when present, passed in-memory by the
        ingest step — read ONLY by the downstream report diagnostic, NEVER by the blind solve. ``None``
        for frames (like DDOTI) that carry no header WCS.
    norad_id : int | None
        The externally-established NORAD id of the trailing satellite (provenance, from meta).
    """

    truth_path: Path
    scored_truth_ra_deg: float
    scored_truth_dec_deg: float
    exposure_mid_utc: dt.datetime
    pointing_wcs: object | None
    norad_id: int | None


def assemble_real_truth(tle, meta: dict, out_dir, pointing_wcs=None) -> RealTruthResult:
    """Assemble + write the SEALED real-frame ``truth.json`` from a committed TLE + frame metadata.

    Reads the exposure timing (``meta['timing']`` ``date_obs``/``exptime_s``) and the observatory
    site (``meta['observatory']`` ``lat_deg``/``lon_deg``/``elev_m``), computes the exposure midpoint,
    propagates ``tle`` to that instant via render's shared ``propagate_satellite_radec`` (topocentric —
    LEO parallax honored), and writes ``<out_dir>/truth.json`` whose ``scored_truth`` is consumed by
    ``score._load_truth`` UNCHANGED. The header WCS (when the frame carries one) + the midpoint are
    returned IN-MEMORY only — never written into a solver image, never fed into the blind solve.

    Parameters
    ----------
    tle : tracklet.scene.TLE
        The committed two-line element set for the trailing satellite.
    meta : dict
        Parsed ``meta.toml`` (``timing``/``observatory``/``satellite`` tables).
    out_dir : str | pathlib.Path
        Directory to write ``truth.json`` into (created if absent).
    pointing_wcs : astropy.wcs.WCS | None
        The frame's header WCS passed in-memory by ingest, or ``None`` when the frame has none.

    Returns
    -------
    RealTruthResult
    """
    from tracklet.render import propagate_satellite_radec

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    timing = meta["timing"]
    obs = meta["observatory"]
    mid = exposure_midpoint_utc(timing["date_obs"], float(timing["exptime_s"]))

    ra_deg, dec_deg = propagate_satellite_radec(
        tle,
        float(obs["lat_deg"]),
        float(obs["lon_deg"]),
        float(obs["elev_m"]),
        mid,
    )

    norad_id = meta.get("satellite", {}).get("norad_id")

    def _iso(d: dt.datetime) -> str:
        return d.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

    start = mid - dt.timedelta(seconds=float(timing["exptime_s"]) / 2.0)
    end = mid + dt.timedelta(seconds=float(timing["exptime_s"]) / 2.0)

    # Schema: `scored_truth` is the EXACT key/shape render._build_truth writes (render.py:321), so
    # score._load_truth consumes this real-frame truth.json with no change. The extra provenance keys
    # below are ignored by score and document the real-frame source for the report/diagnostic.
    truth = {
        "scored_truth": {"ra_deg": float(ra_deg), "dec_deg": float(dec_deg)},
        "satellite": {"mid": {"ra_deg": float(ra_deg), "dec_deg": float(dec_deg)}},
        "exposure": {
            "start_utc": _iso(start),
            "mid_utc": _iso(mid),
            "end_utc": _iso(end),
            "exposure_s": float(timing["exptime_s"]),
        },
        "source": "real-frame (M1): TLE -> skyfield topocentric @ exposure midpoint",
        "norad_id": norad_id,
        "observatory": {
            "lat_deg": float(obs["lat_deg"]),
            "lon_deg": float(obs["lon_deg"]),
            "elev_m": float(obs["elev_m"]),
        },
        "header_wcs_present": pointing_wcs is not None,
    }

    truth_path = out / "truth.json"
    with open(truth_path, "w") as fh:
        json.dump(truth, fh, indent=2, sort_keys=True)

    return RealTruthResult(
        truth_path=truth_path,
        scored_truth_ra_deg=float(ra_deg),
        scored_truth_dec_deg=float(dec_deg),
        exposure_mid_utc=mid,
        pointing_wcs=pointing_wcs,
        norad_id=int(norad_id) if norad_id is not None else None,
    )
