"""tdm — CCSDS TDM (RADEC) output writer (M2 Sprint 2).

Contract: ``write_tdm(result, epoch_utc, station, out_path) -> Path``.

A pure, downstream-of-``score`` artifact writer, SYMMETRIC to ``report.write_report``: it receives the
measured RA/Dec (via the in-memory ``ScoreResult.measured`` ICRS SkyCoord), the exposure-MIDPOINT epoch
(computed in ``run``), and the ``PARTICIPANT_1`` station identifier — all IN-MEMORY — and TEXT-FORMATS a
CCSDS Tracking Data Message. It NEVER opens the sealed answer, never deserializes JSON (no ``json.load``
/ ``json.loads``), and never reaches for the score module's private truth loader. ``score`` stays the
sole reader of ``truth.json``; this writer is auto-covered green by the repo-wide AST guard
``tests/test_seal.py::test_json_load_only_in_score_across_src`` (it contains no JSON deserialize), and no
solving module imports/names it (pinned by ``test_seal.py``'s extended static guard). (Pinned by
tests/test_tdm.py + tests/test_seal.py.)

The emitted file is a CCSDS TDM 503.0-B-2 RADEC message:

  * ``CCSDS_TDM_VERS`` header line;
  * a ``META_START`` … ``META_STOP`` block: ``TIME_SYSTEM = UTC``, ``PARTICIPANT_1 = <station>``,
    ``MODE = SEQUENTIAL``, ``ANGLE_TYPE = RADEC``, ``REF_FRAME = EME2000``;
  * a ``DATA_START`` … ``DATA_STOP`` block: ``<epoch> ANGLE_1 = <ra_deg>`` and
    ``<epoch> ANGLE_2 = <dec_deg>`` (RA = ANGLE_1, Dec = ANGLE_2, per the RADEC angle-type convention),
    where ``<epoch>`` is the exposure-MIDPOINT instant (the scored instant) in ISO-UTC.

The angles are the IN-MEMORY recovered position (``result.measured``, ICRS) — the same independently
measured RA/Dec the residual is scored from — never the sealed truth.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

_TDM_VERSION = "2.0"  # CCSDS TDM 503.0-B-2


def _format_epoch(epoch_utc: dt.datetime) -> str:
    """A timezone-aware UTC instant -> CCSDS ISO-UTC epoch string (``...Z``), mirroring render's
    ``mid_utc`` formatting (``isoformat()`` with the ``+00:00`` -> ``Z`` convention)."""
    return epoch_utc.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def write_tdm(result, epoch_utc: dt.datetime, station: str, out_path) -> Path:
    """Write a CCSDS TDM (RADEC) message for one measured position -> ``out_path``; return the path.

    Parameters
    ----------
    result : score.ScoreResult
        The scored record. Only the IN-MEMORY ``result.measured`` (ICRS SkyCoord — the independent
        recovery) is read for the angles; the sealed truth is NEVER opened here.
    epoch_utc : datetime.datetime
        The exposure-MIDPOINT instant (the scored instant), timezone-aware UTC. Computed in ``run``
        (synthetic: ``scene.utc`` start + ``exposure_s``/2; real: ``rt.exposure_mid_utc``).
    station : str
        The ``PARTICIPANT_1`` ground-station / observatory identifier (``"TRACKLET-SYNTH"`` for the
        synthetic scene; ``meta["observatory"]["name"]`` for the real path).
    out_path : Path | str
        Destination for the ``.tdm`` file (e.g. ``out/track.tdm``).

    Returns
    -------
    Path
        The path written (``Path(out_path)``).
    """
    measured = result.measured.icrs
    ra_deg = float(measured.ra.deg)
    dec_deg = float(measured.dec.deg)
    epoch = _format_epoch(epoch_utc)

    lines = [
        f"CCSDS_TDM_VERS = {_TDM_VERSION}",
        "META_START",
        "TIME_SYSTEM       = UTC",
        f"PARTICIPANT_1     = {station}",
        "MODE              = SEQUENTIAL",
        "PATH              = 1",
        "ANGLE_TYPE        = RADEC",
        "REF_FRAME         = EME2000",
        "META_STOP",
        "DATA_START",
        f"{epoch} ANGLE_1 = {ra_deg!r}",
        f"{epoch} ANGLE_2 = {dec_deg!r}",
        "DATA_STOP",
        "",
    ]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    return out
