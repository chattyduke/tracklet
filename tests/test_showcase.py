"""M2 Sprint 5 — the static, zero-backend showcase page (ACs 5.1, 5.2, 5.2b, 5.3).

The showcase is a STATIC HTML snapshot of the precomputed M1 real-frame result. It serves no
backend, takes no input, and recomputes nothing — `scripts/build_showcase.py` reads a committed
honest display snapshot (`showcase/data/m1_result.json`) and text-templates `showcase/index.html`.

The load-bearing Poka-Yoke: the generator lives in `scripts/`, OUTSIDE `src/tracklet/`, so it may
freely `json.load` its DISPLAY data without tripping the repo-wide `json.load`-only-in-`score` seal
guard (which AST-scans only `src/tracklet/*.py`). The display data is a snapshot of a real M1 run —
it is NOT the sealed `truth.json` and is NOT recomputed by the page.

Every figure on the page is anchored to the canonical M1 provenance (`tests/fixtures/real/PROVENANCE.md`)
by a NUMERIC parse-and-compare anti-drift test (AC 5.2b), so the frozen display data can never silently
diverge from the real run that produced it (a fresh clone has no frame to recompute from).
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_GENERATOR = _REPO / "scripts" / "build_showcase.py"
_DATA = _REPO / "showcase" / "data" / "m1_result.json"
_INDEX = _REPO / "showcase" / "index.html"
_NOTICE = _REPO / "showcase" / "NOTICE"
_PROVENANCE = _REPO / "tests" / "fixtures" / "real" / "PROVENANCE.md"
_SRC = _REPO / "src" / "tracklet"

# Networking / server / backend module tokens that a STATIC, zero-backend generator (and its
# emitted page) must never import or reference (AC 5.1).
_BACKEND_TOKENS = (
    "socket",
    "http",
    "urllib",
    "requests",
    "flask",
    "fastapi",
    "wsgi",
    "asgi",
    "django",
    "bottle",
    "tornado",
    "aiohttp",
    "websocket",
)


def _build() -> Path:
    """Run the generator (idempotent) and return the emitted index.html path."""
    result = subprocess.run(
        [sys.executable, str(_GENERATOR)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"build_showcase.py failed (rc={result.returncode}):\n{result.stdout}\n{result.stderr}"
    )
    assert _INDEX.exists(), "build_showcase.py did not emit showcase/index.html"
    return _INDEX


@pytest.fixture(scope="module")
def page_html() -> str:
    return _build().read_text(encoding="utf-8")


# === Helpers: parse canonical numbers out of PROVENANCE.md (AC 5.2b) ============================
# PROVENANCE records figures with `≈` prefixes and dual-precision forms (e.g. `(305.557°, −14.964°)`
# in the smoke table vs `(305.5565, −14.9640)` in the §C1 line; `≈ 4956 px`). We parse the NUMBERS
# and compare numerically, never byte-for-byte. The canonical anchors are the §C1-camera-offset line
# (the `(305.5565, −14.9640)` four-decimal form) + the milestone-residual / TLE-age / AC-4.6 lines.

_PROV_TEXT = _PROVENANCE.read_text(encoding="utf-8")


def _provenance_center() -> tuple[float, float]:
    """The target frame's own blind-recovered center from the §C1 line:
    '... overlaps the expected center to 0.0002° ... blind-recovered center (305.5565, −14.9640)'.
    Parse the four-decimal `(305.5565, −14.9640)` form (NOT the smoke table's 3-decimal form)."""
    # Match `(305.5565, −14.9640)` — note PROVENANCE uses a U+2212 MINUS for the Dec.
    m = re.search(r"\(305\.5565,\s*[−\-]14\.9640\)", _PROV_TEXT)
    assert m, "could not find the canonical (305.5565, -14.9640) recovered-center form in PROVENANCE.md"
    ra = 305.5565
    dec = -14.9640
    return ra, dec


def _provenance_residual() -> float:
    """The milestone residual '315.52″' from the milestone-residual section."""
    m = re.search(r"M1 numeric residual\s*\n?\s*=\s*315\.52", _PROV_TEXT) or re.search(
        r"315\.52", _PROV_TEXT
    )
    assert m, "could not find the 315.52 milestone residual in PROVENANCE.md"
    return 315.52


def _provenance_detect() -> tuple[float, float]:
    """Trail length + angle: '≈ 4956 px @ 126.16°'."""
    m = re.search(r"4956\s*px\s*@\s*126\.16", _PROV_TEXT)
    assert m, "could not find '4956 px @ 126.16' detect figures in PROVENANCE.md"
    return 4956.0, 126.16


def _provenance_tle_age() -> float:
    """TLE age before exposure midpoint: '0.598 d'."""
    m = re.search(r"0\.598\s*d", _PROV_TEXT)
    assert m, "could not find the 0.598 d TLE age in PROVENANCE.md"
    return 0.598


def _provenance_sep() -> float:
    """AC-4.6 separation: 'overlaps ... to 0.0002°'."""
    m = re.search(r"0\.0002", _PROV_TEXT)
    assert m, "could not find the 0.0002 AC-4.6 separation in PROVENANCE.md"
    return 0.0002


# === AC 5.2b: anti-drift anchor — committed display JSON == canonical PROVENANCE figures =========


def test_ac52b_display_data_matches_provenance_numerically():
    """The committed `showcase/data/m1_result.json` figures EQUAL the canonical PROVENANCE figures,
    compared NUMERICALLY after parsing (not a byte-match — PROVENANCE uses `≈`/dual-precision forms).
    So the frozen display data (a fresh clone has no real frame to recompute) can never silently
    diverge from the real M1 run that produced it."""
    data = json.loads(_DATA.read_text(encoding="utf-8"))

    prov_residual = _provenance_residual()
    prov_ra, prov_dec = _provenance_center()
    prov_len, prov_angle = _provenance_detect()
    prov_tle = _provenance_tle_age()
    prov_sep = _provenance_sep()

    # Residual: PROVENANCE records 315.52 (2 dp); the JSON freezes the exact out_real value
    # (315.523604). They must agree to PROVENANCE's recorded precision.
    assert abs(data["residual_arcsec"] - prov_residual) < 0.01, (
        f"residual {data['residual_arcsec']} drifted from PROVENANCE {prov_residual}"
    )
    assert abs(data["recovered_center_ra_deg"] - prov_ra) < 1e-4, (
        f"recovered RA {data['recovered_center_ra_deg']} drifted from PROVENANCE {prov_ra}"
    )
    assert abs(data["recovered_center_dec_deg"] - prov_dec) < 1e-4, (
        f"recovered Dec {data['recovered_center_dec_deg']} drifted from PROVENANCE {prov_dec}"
    )
    assert abs(data["detect_length_px"] - prov_len) < 1.0, (
        f"detect length {data['detect_length_px']} drifted from PROVENANCE {prov_len}"
    )
    assert abs(data["detect_angle_deg"] - prov_angle) < 0.01, (
        f"detect angle {data['detect_angle_deg']} drifted from PROVENANCE {prov_angle}"
    )
    assert abs(data["tle_age_days"] - prov_tle) < 1e-3, (
        f"TLE age {data['tle_age_days']} drifted from PROVENANCE {prov_tle}"
    )
    assert abs(data["plausibility_separation_deg"] - prov_sep) < 1e-4, (
        f"AC-4.6 separation {data['plausibility_separation_deg']} drifted from PROVENANCE {prov_sep}"
    )

    # The five degradation sources must be present and TLE-age must be flagged dominant.
    sources = data["degradation_sources"]
    assert len(sources) == 5, f"expected 5 degradation sources, got {len(sources)}"
    assert sources[0]["dominant"] is True, "the first degradation source must be flagged dominant"
    assert "tle" in sources[0]["name"].lower(), (
        f"the dominant degradation source must be the TLE-age term; got {sources[0]['name']!r}"
    )


# === AC 5.1: zero-backend / no-recompute / static =============================================


def test_ac51_generator_has_no_backend_or_network_import():
    """The generator AST imports no socket/http/urllib/requests/flask/wsgi/server module — it is a
    pure static-site templater that reads committed local files only (no fetch, no server)."""
    tree = ast.parse(_GENERATOR.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    for name in imported:
        top = name.split(".")[0]
        assert top not in _BACKEND_TOKENS, (
            f"build_showcase.py imports backend/network module {name!r} — it must be zero-backend"
        )


def test_ac51_generator_reads_only_committed_local_files():
    """Static-proof that the generator names no http(s):// URL and no network call — it reads the
    committed display JSON + writes the static HTML, nothing else. (A network fetch would put a
    scheme literal or a network module in the source; both are asserted absent.)"""
    source = _GENERATOR.read_text(encoding="utf-8")
    assert "http://" not in source and "https://" not in source, (
        "build_showcase.py must not contain a network URL — it reads only committed local files"
    )
    # No backend/network token even as a string reference.
    for token in ("flask", "fastapi", "wsgi", "asgi", "django", "socket.socket"):
        assert token not in source, f"build_showcase.py references backend token {token!r}"


def test_ac51_emitted_page_has_no_script_or_backend(page_html: str):
    """The emitted page is pure static HTML: no <script>, no <form>, no backend/network reference —
    it recomputes nothing, takes no input, and serves no compute. Opens over file:// with no server."""
    lower = page_html.lower()
    assert "<script" not in lower, "the showcase page must contain no <script> (zero compute, static)"
    assert "<form" not in lower, "the showcase page must take no input (no <form>)"
    assert "http-equiv=\"refresh\"" not in lower, "no meta-refresh / auto-fetch"
    for token in ("flask", "fastapi", "websocket", "fetch(", "xmlhttprequest"):
        assert token not in lower, f"the showcase page references backend/fetch token {token!r}"


# === AC 5.2: the page shows the honest numbers + honest framing + attribution ===================


def test_ac52_page_shows_honest_residual_and_framing(page_html: str):
    """The page shows the honest M1 numbers verbatim (315.52″) + the TLE-age-dominant framing + the
    non-circular C1-offset note — it does NOT flatter the result."""
    assert "315.52" in page_html, "the page must show the honest 315.52″ residual"
    low = page_html.lower()
    # TLE-age-dominant framing.
    assert "tle" in low and "along-track" in low, "the page must state the TLE-age along-track framing"
    assert "dominant" in low, "the page must state the TLE-age term is dominant"
    # NOT a synthetic-gate pass — honest framing, not flattery.
    assert ("not" in low and "gate" in low), (
        "the page must state this is NOT a synthetic-gate pass"
    )
    # Blind-solved, no prior.
    assert "blind" in low, "the page must state the frame was blind-solved"
    assert "prior" in low or "no position" in low, "the page must state there was no position prior"
    # Non-circular C1 offset.
    assert "non-circular" in low or "noncircular" in low or "non circular" in low, (
        "the page must include the non-circular C1-offset note"
    )


def test_ac52_page_has_ccby_zenodo_attribution(page_html: str):
    """The page carries the CC-BY-4.0 DDOTI / Zenodo-8102655 attribution."""
    assert "CC-BY-4.0" in page_html or "CC BY 4.0" in page_html, "missing CC-BY-4.0 attribution"
    assert "8102655" in page_html, "missing the Zenodo 8102655 record id"
    low = page_html.lower()
    assert "bluewalker" in low or "ddoti" in low, "missing the DDOTI/BlueWalker-3 frame attribution"


def test_ac52_notice_file_committed_with_ccby_attribution():
    """`showcase/NOTICE` is committed unconditionally and attributes the source frame under CC-BY-4.0
    (present whether or not the optional overlay thumbnail is committed)."""
    assert _NOTICE.exists(), "showcase/NOTICE must be committed unconditionally"
    text = _NOTICE.read_text(encoding="utf-8")
    assert "CC-BY-4.0" in text or "CC BY 4.0" in text, "NOTICE must state CC-BY-4.0"
    assert "8102655" in text, "NOTICE must name the Zenodo 8102655 record"


# === AC 5.3: the generator lives outside src/ so the seal guard stays ["score.py"] ===============


def test_ac53_generator_lives_outside_src_tracklet():
    """The generator is in `scripts/`, NOT `src/tracklet/` — the load-bearing seal Poka-Yoke. So it
    may `json.load` its display data without the repo-wide `json.load`-only-in-score guard ever seeing
    it (that guard scans only `src/tracklet/*.py`)."""
    assert _GENERATOR.exists(), "scripts/build_showcase.py must exist"
    assert not (_SRC / "build_showcase.py").exists(), (
        "build_showcase.py must NOT live under src/tracklet/ — it would couple to the src-only seal guard"
    )
    # And it genuinely deserializes JSON (the thing that would trip the guard if it were in src/).
    source = _GENERATOR.read_text(encoding="utf-8")
    assert "json.load" in source, (
        "build_showcase.py is expected to json.load its display data (that's why it lives in scripts/)"
    )


def test_ac53_seal_guard_still_reports_only_score():
    """The repo-wide json.load guard still reports EXACTLY ['score.py'] across src/ — proving the
    showcase generator's json.load (in scripts/) did not leak a new truth-deserializer into src/."""
    json_modules: list[str] = []
    for py in sorted(_SRC.glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        aliases: set[str] = set()
        deserializes = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "json":
                        aliases.add(alias.asname or "json")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "json" and any(a.name in ("load", "loads") for a in node.names):
                    deserializes = True
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("load", "loads")
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in aliases
            ):
                deserializes = True
        if deserializes:
            json_modules.append(py.name)
    assert json_modules == ["score.py"], (
        f"json.load/json.loads must appear only in score.py across src/; found {json_modules}"
    )
