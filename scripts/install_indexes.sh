#!/usr/bin/env bash
#
# install_indexes.sh — S0 plate-solver gate (the project's #1 setup risk).
#
# Fetches the astrometry.net 4100-series WIDE-FIELD index subset that matches tracklet's ~2.8 deg
# field, drops it into an index dir, and points astrometry.cfg at it. The exact useful subset is
# confirmed empirically by the smoke solve (see `make test-golden` / the @solver smoke test) — this
# script installs a superset spanning ~22'..240' quads (10-100%+ of the 168' field).
#
# Andon HARD STOP (plan 4.2 #4): a failed index fetch is NOT a degraded mode — it exits non-zero
# and S0 stops. Recovery: retry a mirror, or run `install_indexes.sh --astap` for the ASTAP fallback.
#
# Footprint (disclosed in README): the index dir (~340 MB) + one additive `add_path` line in
# astrometry.cfg. Uninstall: rm -rf the index dir and revert that line.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX_DIR="${TRACKLET_INDEX_DIR:-$REPO_DIR/indexes}"
BASE_URL="${TRACKLET_INDEX_BASE_URL:-https://data.astrometry.net/4100}"
# 4100-series single-file all-sky wide-field indexes (verified single-file, not healpix-tiled).
SCALES=(4107 4108 4109 4110 4111 4112 4113)

find_cfg() {
  local c
  c="$(find /opt/homebrew /usr/local -name astrometry.cfg 2>/dev/null | head -1 || true)"
  echo "${c:-/opt/homebrew/etc/astrometry.cfg}"
}

install_astap() {
  # ASTAP fallback — executable recovery path if the astrometry.net mirrors are unreachable.
  # macOS arm64: downloads the CLI + the d50 star database, codesigns the unsigned binary, verifies.
  echo "ASTAP fallback (recovery path — use only if data.astrometry.net is down):"
  local dir="${TRACKLET_ASTAP_DIR:-$REPO_DIR/astap}"
  mkdir -p "$dir"
  echo "  1) Download CLI + d50 DB into $dir:"
  echo "     curl -fSL -o $dir/astap_cli.zip https://downloads.sourceforge.net/project/astap-program/astap_command_line_version/astap_cli_macos.zip"
  echo "     curl -fSL -o $dir/d50.zip       https://downloads.sourceforge.net/project/astap-program/star_databases/d50_star_database.zip"
  echo "  2) Unzip both; then codesign the unsigned binary so macOS will run it:"
  echo "     codesign --force -s - $dir/astap"
  echo "  3) Verify on the smoke field:  $dir/astap -f <smoke.fits> -wcs  ->  a .wcs astropy can read."
  echo "  (Not auto-run: the astrometry.net path is primary and working. This is the documented"
  echo "   recovery path per AC-0.6 — promote to a real install only if the primary path fails.)"
}

if [[ "${1:-}" == "--astap" ]]; then
  install_astap
  exit 0
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "usage: install_indexes.sh [--astap] [--help]"
  echo "  (no args)  fetch the 4100-series wide-field indexes + wire astrometry.cfg"
  echo "  --astap    print the ASTAP fallback recovery steps"
  exit 0
fi

mkdir -p "$INDEX_DIR"
echo "Fetching 4100-series wide-field indexes (${SCALES[*]}) -> $INDEX_DIR"
for s in "${SCALES[@]}"; do
  f="index-$s.fits"
  if [[ -s "$INDEX_DIR/$f" ]]; then echo "  have   $f"; continue; fi
  echo "  fetch  $f ..."
  if ! curl -fSL --retry 3 --retry-delay 2 -o "$INDEX_DIR/$f.part" "$BASE_URL/$f"; then
    echo "" >&2
    echo "ERROR: failed to fetch $BASE_URL/$f" >&2
    echo "Andon HARD STOP (plan 4.2 #4): astrometry.net unreachable / 404 / rate-limited." >&2
    echo "  Recovery: retry later, OR run: $0 --astap" >&2
    rm -f "$INDEX_DIR/$f.part"
    exit 1
  fi
  mv "$INDEX_DIR/$f.part" "$INDEX_DIR/$f"
done

CFG="$(find_cfg)"
if ! grep -qxF "add_path $INDEX_DIR" "$CFG" 2>/dev/null; then
  printf '\n# tracklet wide-field indexes (added by install_indexes.sh)\nadd_path %s\n' "$INDEX_DIR" >> "$CFG"
  echo "appended 'add_path $INDEX_DIR' to $CFG"
else
  echo "astrometry.cfg already points at $INDEX_DIR"
fi
grep -qE '^\s*autoindex' "$CFG" 2>/dev/null || echo "autoindex" >> "$CFG"

echo "Done. Installed indexes:"
ls -lh "$INDEX_DIR"/index-*.fits
