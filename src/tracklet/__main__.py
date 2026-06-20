"""``python -m tracklet`` entry point — symmetric to the ``tracklet`` console script.

Reuses ``run.main`` VERBATIM (it already returns an int rc and defaults to ``sys.argv``); this shim
adds no pipeline logic and reads no truth, so the sealed-truth seal is untouched (the sole truth
deserializer stays in ``score.py``).
"""
from __future__ import annotations

from .run import main

if __name__ == "__main__":
    raise SystemExit(main())
