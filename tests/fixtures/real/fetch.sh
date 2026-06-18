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
# Usage:   tests/fixtures/real/fetch.sh [OUT_DIR]
#   OUT_DIR defaults to tests/fixtures/real/. Produces:
#     $OUT_DIR/20221118T024706C1o.fits.fz   (Rice-compressed, member-SHA256-verified)
#     $OUT_DIR/20221118T024706C1o.fits      (plain FITS, funpacked — what the pipeline consumes)
#
# The .fits / .fits.fz are gitignored (see repo .gitignore: *.fits) — fetch on demand, never committed.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-$HERE}"
mkdir -p "$OUT_DIR"

MEMBER="BW3_DDOTI_data/20221118/20221118T024706C1o.fits.fz"
MEMBER_SHA256="b6dcf797163fab78adca9316f0dcb18eb29e83c8c398ae325a292fad30519ca1"
MEMBER_SIZE_BYTES=17507520

# Two urls: primary Zenodo API (DOI 10.5281/zenodo.8102655) + documented mirror (Zenodo legacy files path).
PRIMARY_URL="https://zenodo.org/api/records/8102655/files/BW3_DDOTI_data.tgz/content"
MIRROR_URL="https://zenodo.org/record/8102655/files/BW3_DDOTI_data.tgz?download=1"

FZ="$OUT_DIR/20221118T024706C1o.fits.fz"
FITS="$OUT_DIR/20221118T024706C1o.fits"

verify_sha256 () {
  local file="$1"
  local got
  if command -v shasum >/dev/null 2>&1; then
    got="$(shasum -a 256 "$file" | awk '{print $1}')"
  else
    got="$(sha256sum "$file" | awk '{print $1}')"
  fi
  [ "$got" = "$MEMBER_SHA256" ]
}

stream_member () {
  # Stream the gzipped tar over HTTP and extract ONLY the one member to $FZ.
  # tar reads the archive on stdin (-f -), -O writes the matched member to stdout.
  # The curl pipe closes once the member is past, so the full 2.4 GB is never fully transferred.
  local url="$1"
  echo "  streaming single member from: $url"
  curl -fsSL --max-time 600 "$url" | tar -xzO -f - "$MEMBER" > "$FZ"
}

echo "fetch.sh: retrieving the M1 real frame ($MEMBER)"
ok=0
for url in "$PRIMARY_URL" "$MIRROR_URL"; do
  if stream_member "$url" && verify_sha256 "$FZ"; then
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
