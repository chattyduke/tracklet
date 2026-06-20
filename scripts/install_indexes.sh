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

# Cross-platform astrometry.cfg resolver (S3, AC 3.1).
#
# Resolution order (first hit wins):
#   1) explicit env override  $TRACKLET_ASTROMETRY_CFG  (CI / clean-room can pin the exact file)
#   2) a known-location probe over the apt/brew layouts: /etc/astrometry.cfg first (the apt
#      `astrometry.net` default on a Linux CI runner), then the brew etc dirs;
#   3) a `find` over the search roots (default: /opt/homebrew /usr/local on mac, /etc /usr/share on
#      Linux) — INJECTABLE: callers (and the unit test) can pass roots as positional args so a
#      stubbed Linux layout under a writable temp root resolves without touching the real filesystem.
# Always emits a non-empty path (a sane default) so the caller has something to wire.
#
# macOS/brew behavior is UNCHANGED: with no env override and no injected roots, the default roots are
# `/opt/homebrew /usr/local` and the brew cfg is found exactly as before.
find_cfg() {
  # 1) explicit override.
  if [[ -n "${TRACKLET_ASTROMETRY_CFG:-}" ]]; then
    echo "$TRACKLET_ASTROMETRY_CFG"
    return 0
  fi

  # Search roots: injected positional args, else the platform defaults.
  local roots=("$@")
  if [[ ${#roots[@]} -eq 0 ]]; then
    if [[ "$(uname -s)" == "Linux" ]]; then
      roots=(/etc /usr/share /usr/local)
    else
      roots=(/opt/homebrew /usr/local)
    fi
  fi

  # 2) probe well-known absolute locations under each root (cheap, deterministic).
  local probe root
  for root in "${roots[@]}"; do
    for probe in "$root/etc/astrometry.cfg" "$root/astrometry.cfg" \
                 "$root/share/astrometry/astrometry.cfg"; do
      if [[ -f "$probe" ]]; then
        echo "$probe"
        return 0
      fi
    done
  done

  # 3) recursive find over the roots (only those that exist), first hit wins.
  local existing=()
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] && existing+=("$root")
  done
  local c=""
  if [[ ${#existing[@]} -gt 0 ]]; then
    c="$(find "${existing[@]}" -name astrometry.cfg 2>/dev/null | head -1 || true)"
  fi

  # Sane default per platform (so the caller always has a path to attempt to wire).
  if [[ -n "$c" ]]; then
    echo "$c"
  elif [[ "$(uname -s)" == "Linux" ]]; then
    echo "/etc/astrometry.cfg"
  else
    echo "/opt/homebrew/etc/astrometry.cfg"
  fi
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

main() {
  if [[ "${1:-}" == "--astap" ]]; then
    install_astap
    exit 0
  fi
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "usage: install_indexes.sh [--astap] [--help]"
    echo "  (no args)  fetch the 4100-series wide-field indexes + wire astrometry.cfg"
    echo "  --astap    print the ASTAP fallback recovery steps"
    echo "  env: TRACKLET_ASTROMETRY_CFG pins the astrometry.cfg to wire (override auto-discovery)"
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
  # Append to the astrometry cfg, escalating with sudo ONLY when it is not directly writable — e.g.
  # the root-owned apt /etc/astrometry.cfg on a Linux CI runner. The macOS brew cfg is user-writable,
  # so no sudo is used there. A cfg that is neither writable nor sudo-writable fails LOUDLY (never a
  # silent skip that would leave solve-field unable to find the indexes).
  _cfg_append() {  # _cfg_append <verbatim-text>
    if [[ -w "$CFG" ]]; then
      printf '%s' "$1" >> "$CFG"
    elif command -v sudo >/dev/null 2>&1; then
      printf '%s' "$1" | sudo tee -a "$CFG" >/dev/null
    else
      echo "ERROR: $CFG is not writable and sudo is unavailable — cannot wire add_path." >&2
      exit 1
    fi
  }
  if ! grep -qxF "add_path $INDEX_DIR" "$CFG" 2>/dev/null; then
    printf -v _add '\n# tracklet wide-field indexes (added by install_indexes.sh)\nadd_path %s\n' "$INDEX_DIR"
    _cfg_append "$_add"
    echo "appended 'add_path $INDEX_DIR' to $CFG"
  else
    echo "astrometry.cfg already points at $INDEX_DIR"
  fi
  if ! grep -qE '^\s*autoindex' "$CFG" 2>/dev/null; then
    printf -v _ai 'autoindex\n'
    _cfg_append "$_ai"
  fi

  echo "Done. Installed indexes:"
  ls -lh "$INDEX_DIR"/index-*.fits
}

# Run the install body only when EXECUTED, not when SOURCED (so find_cfg/install_astap are unit
# testable in isolation — Poka-Yoke: sourcing must have NO side effects). The standard bash idiom.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
