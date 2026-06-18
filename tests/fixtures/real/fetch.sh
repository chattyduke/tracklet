#!/usr/bin/env bash
# fetch.sh — stranger-reproducible retrieval of the M1 real frame (BlueWalker-3 / DDOTI).
#
# The frame lives inside a 2.4 GB archive on Zenodo. This script STREAMS the archive and extracts
# ONLY the single 17.5 MB member we need (never landing the 2.4 GB on disk — a deliberate disk-Andon
# Kaizen), verifies the member against a PINNED SHA256, then funpacks the Rice-compressed .fits.fz to
# a plain FITS the pipeline can read.
#
# Reproducibility survives CDN/URL rot via TWO urls: the primary Zenodo API + a documented mirror.
# The integrity guarantee is the pinned MEMBER_SHA256 (not the url) — whichever url serves the bytes,
# the SHA256 must match or the script fails loud.
#
# Usage:
#   tests/fixtures/real/fetch.sh [OUT_DIR]
#       Default. Fetch + SHA256-verify + funpack the single pinned M1 target frame.
#       OUT_DIR defaults to tests/fixtures/real/. Produces:
#         $OUT_DIR/20221118T024706C1o.fits.fz   (Rice-compressed, member-SHA256-verified)
#         $OUT_DIR/20221118T024706C1o.fits      (plain FITS, funpacked — what the pipeline consumes)
#
#   tests/fixtures/real/fetch.sh --offset-frames [OUT_DIR]
#       ALSO fetch the 3 OTHER same-night DDOTI C1 frames (024735 / 024757 / 024816) used to derive
#       the non-circular C1 camera offset for the AC-4.6 plausibility gate. All 3 members are extracted
#       in ONE archive read (tar pulls them in archive order during a single stream), then funpacked.
#
#       WHY ONE STREAM, NEVER PARALLEL (lesson learned): 3 concurrent curl streams of the same 2.4 GB
#       archive STALL at 0 bytes for 8+ minutes under Zenodo server-side range-read contention. A single
#       stream completes; and extracting all 3 members in that one pass pays the deep 2.4 GB seek ONCE
#       instead of once per frame. Do NOT parallelize, and do NOT re-stream per member.
#
#       These 3 members have NO pinned SHA256 (the target is the only integrity anchor), so the gate
#       is: member extracted, non-empty, and funpacks to a valid FITS. Each frame's SHA256 + byte
#       size is printed so it can be pinned in a future tick if desired.
#
#   tests/fixtures/real/fetch.sh -h | --help    Show usage.
#
# The .fits / .fits.fz are gitignored (see repo .gitignore: *.fits) — fetch on demand, never committed.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage () {
  cat <<'EOF'
Usage:
  fetch.sh [OUT_DIR]                   Fetch + SHA256-verify + funpack the pinned M1 target frame (default).
  fetch.sh --offset-frames [OUT_DIR]   ALSO fetch the 3 same-night DDOTI C1 offset frames in ONE
                                       stream (one deep seek for all 3; never parallel), funpacking each.
                                       Used to derive the non-circular C1 camera offset for the AC-4.6 gate.
  fetch.sh -h | --help                 Show this help.

OUT_DIR defaults to the script's own directory (tests/fixtures/real/).
Fetched .fits / .fits.fz are gitignored — never committed.
EOF
}

# ---- arg parsing: optional --offset-frames flag, optional OUT_DIR positional ----
OFFSET_MODE=0
OUT_DIR="$HERE"
for arg in "$@"; do
  case "$arg" in
    --offset-frames) OFFSET_MODE=1 ;;
    -h|--help)       usage; exit 0 ;;
    -*)              echo "fetch.sh: unknown option: $arg" >&2; usage >&2; exit 2 ;;
    *)               OUT_DIR="$arg" ;;
  esac
done
mkdir -p "$OUT_DIR"

MEMBER="BW3_DDOTI_data/20221118/20221118T024706C1o.fits.fz"
MEMBER_SHA256="b6dcf797163fab78adca9316f0dcb18eb29e83c8c398ae325a292fad30519ca1"
MEMBER_SIZE_BYTES=17507520

# The 3 OTHER same-night DDOTI C1 frames (after the 024706 target) — fetched only in --offset-frames mode.
OFFSET_MEMBERS=(
  "BW3_DDOTI_data/20221118/20221118T024735C1o.fits.fz"
  "BW3_DDOTI_data/20221118/20221118T024757C1o.fits.fz"
  "BW3_DDOTI_data/20221118/20221118T024816C1o.fits.fz"
)

# Two urls: primary Zenodo API (DOI 10.5281/zenodo.8102655) + documented mirror (Zenodo legacy files path).
PRIMARY_URL="https://zenodo.org/api/records/8102655/files/BW3_DDOTI_data.tgz/content"
MIRROR_URL="https://zenodo.org/record/8102655/files/BW3_DDOTI_data.tgz?download=1"

FZ="$OUT_DIR/20221118T024706C1o.fits.fz"
FITS="$OUT_DIR/20221118T024706C1o.fits"

sha256_of () {
  local file="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    sha256sum "$file" | awk '{print $1}'
  fi
}

verify_sha256 () {
  # default-path integrity gate: member bytes must match the PINNED target SHA256.
  [ "$(sha256_of "$1")" = "$MEMBER_SHA256" ]
}

stream_member () {
  # Stream the gzipped tar over HTTP and extract ONLY one member to an output file.
  # tar reads the archive on stdin (-f -), -O writes the matched member to stdout.
  # The curl pipe closes once the member is past, so the full 2.4 GB is never fully transferred.
  # ALWAYS one stream at a time — never run two of these concurrently against the same archive.
  local url="$1" member="$2" out="$3"
  echo "  streaming single member from: $url"
  curl -fsSL --max-time 600 "$url" | tar -xzO -f - "$member" > "$out"
}

fetch_offset_members_onepass () {
  # SINGLE-PASS extraction of ALL offset members in ONE stream of the archive. tar extracts the named
  # members in archive order during one read, so the deep 2.4 GB seek happens ONCE — not once per frame.
  # (Measured: one pass reaching the last member ~30 min; three separate passes would triple the deep
  # seek.) The members come out into a temp dir, then are moved into OUT_DIR and funpacked.
  # No pinned SHA256 exists for these (the target is the only integrity anchor), so the gate is:
  # member extracted, non-empty, and funpacks to a valid FITS. Each frame's SHA256 + size is printed.
  local td member fz fits
  td="$(mktemp -d)"
  local got=0
  for url in "$PRIMARY_URL" "$MIRROR_URL"; do
    echo "  one-pass stream from: $url"
    # tar exits after the LAST named member is read, closing the pipe (curl gets SIGPIPE — expected).
    curl -fsSL --max-time 3600 "$url" 2>/dev/null | tar -xz -C "$td" "${OFFSET_MEMBERS[@]}" 2>/dev/null || true
    local n
    n="$(find "$td" -name '*C1o.fits.fz' | wc -l | tr -d ' ')"
    echo "  extracted $n/${#OFFSET_MEMBERS[@]} members"
    if [ "$n" -eq "${#OFFSET_MEMBERS[@]}" ]; then got=1; break; fi
    echo "  url incomplete — trying next url" >&2
  done
  if [ "$got" -ne 1 ]; then
    echo "ERROR: could not retrieve all offset members from either url." >&2
    rm -rf "$td"
    return 1
  fi
  for member in "${OFFSET_MEMBERS[@]}"; do
    fz="$OUT_DIR/$(basename "$member")"
    fits="$OUT_DIR/$(basename "$member" .fz)"
    cp "$td/$member" "$fz"
    rm -f "$fits"
    funpack -O "$fits" "$fz"
    echo "  $(basename "$member"): funpacked -> $fits"
    echo "    sha256=$(sha256_of "$fz")  bytes=$(wc -c < "$fz" | tr -d ' ')"
  done
  rm -rf "$td"
}

# ---- --offset-frames mode: single-pass multi-member fetch (early exit; does NOT touch the target path) ----
if [ "$OFFSET_MODE" -eq 1 ]; then
  echo "fetch.sh: offset-frame mode — ${#OFFSET_MEMBERS[@]} same-night DDOTI C1 frames in ONE stream."
  echo "  One archive read extracts all ${#OFFSET_MEMBERS[@]} members (in archive order), so the deep"
  echo "  2.4 GB seek happens ONCE. NEVER parallelize concurrent streams of this archive: 3 parallel"
  echo "  range-reads STALL at 0 bytes for 8+ min under Zenodo server-side contention (observed); a"
  echo "  single stream completes. These frames derive the non-circular C1 camera offset (AC 4.6)."
  fetch_offset_members_onepass
  echo ""
  echo "done. ${#OFFSET_MEMBERS[@]} offset frames funpacked into $OUT_DIR (gitignored; re-derive with _derive_offset.py)"
  exit 0
fi

# ---- default single-target path (unchanged) ----
echo "fetch.sh: retrieving the M1 real frame ($MEMBER)"
ok=0
for url in "$PRIMARY_URL" "$MIRROR_URL"; do
  if stream_member "$url" "$MEMBER" "$FZ" && verify_sha256 "$FZ"; then
    ok=1
    echo "  member SHA256 verified: $MEMBER_SHA256"
    break
  fi
  echo "  url failed or SHA256 mismatch — trying next url" >&2
done

if [ "$ok" -ne 1 ]; then
  echo "ERROR: could not retrieve a SHA256-matching member from either url." >&2
  echo "       expected SHA256 $MEMBER_SHA256 ($MEMBER_SIZE_BYTES bytes)." >&2
  rm -f "$FZ"
  exit 1
fi

echo "funpack -> plain FITS: $FITS"
funpack -O "$FITS" "$FZ"
echo "done. plain FITS at $FITS"
