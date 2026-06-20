#!/usr/bin/env bash
#
# clean_room_reproduce.sh — the autonomous CLEAN-MACHINE reproduce proof (M2 S3, AC 3.2-3.4).
#
# Proves clone -> install -> reproduce UNAIDED on a fresh same-arch environment:
#   1) a fresh temp dir + `git clone` of the COMMITTED HEAD of this repo (only committed work is
#      proven — run on a clean tree),
#   2) a fresh `python3.14 -m venv` (NEVER the dev .venv),
#   3) a NON-editable `pip install . -c requirements.lock` (the exact-reproduce constraints file),
#   4) the INSTALLED `tracklet` CLI runs the synthetic scene -> residual < 10" (echoed),
#   5) `pytest -m "not solver"` from the INSTALLED package (not the clone's src/) -> green.
#
# It reuses the HOST's documented `solve-field` + wired ~340 MB indexes (the @solver toolchain) — it
# tests the PACKAGE install + reproduce, NOT the solver install. If the host lacks either, it prints a
# loud remediation and exits non-zero (an honest red, never a misleading silent pass).
#
# Hermetic: a trap tears down the temp dir on ANY exit; it writes nothing outside its temp dir; it
# reads the host indexes read-only; it NEVER pushes. The clone carries the committed data/ fixtures,
# and the installed CLI is pointed at them via TRACKLET_DATA (a non-editable wheel lands in
# site-packages where the __file__-relative data/ is absent — this export is load-bearing).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESIDUAL_GATE_ARCSEC=10.0   # reuses score.RESIDUAL_THRESHOLD_ARCSEC — NO new threshold.

say() { printf '\n=== %s ===\n' "$*"; }
die() { printf '\nCLEAN-ROOM ANDON HALT: %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 0) Host preconditions (the @solver toolchain) — loud remediation if absent.
# ---------------------------------------------------------------------------
say "0) host preconditions (solve-field + wired indexes)"
if ! command -v solve-field >/dev/null 2>&1; then
  die "solve-field not found on PATH.
  This clean-room tests the PACKAGE install + reproduce — it needs the host solver already installed.
  Remediation:
    macOS:  brew install astrometry-net
    Linux:  sudo apt-get install -y astrometry.net
  Then wire the indexes:  ./scripts/install_indexes.sh
  (re-run this script once solve-field + indexes are present.)"
fi
echo "  solve-field: $(command -v solve-field)  ($(solve-field --version 2>&1 | head -1))"

if ! ls "$REPO_DIR"/indexes/index-*.fits >/dev/null 2>&1; then
  die "no wired astrometry index files under $REPO_DIR/indexes/.
  Remediation:  ./scripts/install_indexes.sh
  (fetches the 4100-series wide-field indexes + wires astrometry.cfg.)"
fi
echo "  indexes:     $(ls "$REPO_DIR"/indexes/index-*.fits | wc -l | tr -d ' ') wired under $REPO_DIR/indexes"

if ! command -v python3.14 >/dev/null 2>&1; then
  die "python3.14 not found on PATH (the pinned interpreter minor).
  Remediation: install Python 3.14 (e.g. python.org installer or your platform package manager)."
fi
echo "  python3.14:  $(command -v python3.14)  ($(python3.14 --version 2>&1))"

# ---------------------------------------------------------------------------
# 1) Hermetic temp dir (trap-cleaned on ANY exit) — never touches the dev .venv.
# ---------------------------------------------------------------------------
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/tracklet-cleanroom.XXXXXX")"
cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT
say "1) hermetic temp dir"
echo "  $TMP_ROOT"

CLONE_DIR="$TMP_ROOT/clone"
VENV_DIR="$TMP_ROOT/venv"
OUT_DIR="$TMP_ROOT/out"

# ---------------------------------------------------------------------------
# 2) Clone the COMMITTED HEAD (a stranger gets exactly what is committed).
# ---------------------------------------------------------------------------
say "2) git clone (committed HEAD only)"
git clone --quiet "$REPO_DIR" "$CLONE_DIR"
echo "  cloned $REPO_DIR -> $CLONE_DIR  (HEAD: $(git -C "$CLONE_DIR" rev-parse --short HEAD))"

# ---------------------------------------------------------------------------
# 3) Fresh python3.14 venv (NOT the dev .venv) + NON-editable install via the lock.
# ---------------------------------------------------------------------------
say "3) fresh python3.14 venv + non-editable install (pip install . -c requirements.lock)"
python3.14 -m venv "$VENV_DIR"
VPY="$VENV_DIR/bin/python"
"$VPY" -m pip install --quiet --upgrade pip
# NON-editable install of the package itself, constrained by the exact lock. Also install pytest from
# the lock so we can run the non-solver suite from the install (pytest is in requirements.lock).
( cd "$CLONE_DIR" && "$VPY" -m pip install --quiet . -c requirements.lock )
"$VPY" -m pip install --quiet pytest -c "$CLONE_DIR/requirements.lock"
echo "  installed tracklet (non-editable) + pytest into the fresh venv"

# Sanity: the installed tracklet must import from SITE-PACKAGES, not the clone's src/ (proves we are
# testing the package, not the repo tree).
TRACKLET_FILE="$("$VPY" -c 'import tracklet, sys; print(tracklet.__file__)')"
case "$TRACKLET_FILE" in
  "$CLONE_DIR"/src/*) die "installed tracklet resolved to the clone src/ ($TRACKLET_FILE) — NOT the wheel. The install is editable or src/ leaked onto sys.path." ;;
  "$VENV_DIR"/*)      echo "  import tracklet -> $TRACKLET_FILE  (site-packages, NON-editable: good)" ;;
  *)                  die "installed tracklet resolved to an unexpected location: $TRACKLET_FILE" ;;
esac
echo "  importlib.metadata version: $("$VPY" -c 'from importlib.metadata import version; print(version("tracklet"))')"

# ---------------------------------------------------------------------------
# 4) The INSTALLED tracklet CLI runs the synthetic scene -> residual < gate.
#    TRACKLET_DATA points at the clone's committed data/ (site-packages has no data/). LOAD-BEARING.
# ---------------------------------------------------------------------------
say "4) installed CLI runs the synthetic scene"
export TRACKLET_DATA="$CLONE_DIR/data"
echo "  TRACKLET_DATA=$TRACKLET_DATA"
# Run from a NEUTRAL dir (the temp root) so the clone's src/ is never implicitly importable.
( cd "$TMP_ROOT" && "$VENV_DIR/bin/tracklet" \
    --config "$CLONE_DIR/config/default_scene.toml" --out "$OUT_DIR" )

RESIDUAL_FILE="$OUT_DIR/residual.txt"
[[ -s "$RESIDUAL_FILE" ]] || die "no residual.txt produced at $RESIDUAL_FILE (the installed CLI did not complete a real residual)."
RESIDUAL="$(tr -d '[:space:]' < "$RESIDUAL_FILE")"
echo "  installed CLI residual: ${RESIDUAL}\" (gate ${RESIDUAL_GATE_ARCSEC}\")"
# Numeric gate via python (portable float compare; reuses the same 10" contract).
"$VPY" - "$RESIDUAL" "$RESIDUAL_GATE_ARCSEC" <<'PYGATE'
import sys
residual = float(sys.argv[1]); gate = float(sys.argv[2])
if not (residual < gate):
    sys.stderr.write(f"\nCLEAN-ROOM ANDON HALT: residual {residual}\" >= gate {gate}\" — reproduce FAILED.\n")
    raise SystemExit(1)
print(f"  RESIDUAL GATE PASS: {residual}\" < {gate}\"")
PYGATE

# ---------------------------------------------------------------------------
# 5) Non-solver suite from the INSTALLED package (not the clone src/).
#    -o pythonpath= clears the clone pyproject's `pythonpath=["src"]` so `import tracklet` resolves to
#    the INSTALLED wheel, proving the PACKAGE (not the repo tree).
# ---------------------------------------------------------------------------
say "5) pytest -m 'not solver' from the INSTALLED package"
( cd "$CLONE_DIR" && TRACKLET_DATA="$CLONE_DIR/data" \
    "$VPY" -m pytest tests -m "not solver" -q -o pythonpath= )

say "CLEAN-ROOM REPRODUCE: PASS"
echo "  clone+venv+non-editable-install reproduced the synthetic residual ${RESIDUAL}\" < ${RESIDUAL_GATE_ARCSEC}\""
echo "  and the non-solver suite is green from the installed package. Temp dir torn down on exit."
