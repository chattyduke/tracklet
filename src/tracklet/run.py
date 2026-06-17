"""run — orchestrator + CLI (S6).

Wires scene -> render -> [solve_pointing, detect_streak] -> measure_position -> score -> report
behind ONE command. Honest failure handling: solve/detect failure -> labelled message + non-zero
exit, never a fabricated residual.
"""
from __future__ import annotations


def main(argv: "list[str] | None" = None) -> int:
    from tracklet._env import assert_supported_python

    assert_supported_python()  # runtime guard: wrong Python minor fails loud before anything else
    raise NotImplementedError("run.main lands in Sprint 6")


if __name__ == "__main__":
    raise SystemExit(main())
