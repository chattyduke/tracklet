"""fetch_fixtures — one-shot: freeze the TLE + Gaia cone snapshots (S1).

Online; run once, then the pipeline runs fully offline against the committed fixtures.
Idempotent + provenance-stamped + output-validated (bad TLE / truncated Gaia -> hard error).
"""
from __future__ import annotations


def main() -> int:
    raise NotImplementedError("fetch_fixtures lands in Sprint 1")


if __name__ == "__main__":
    raise SystemExit(main())
