"""Runtime Python-version guard.

The validated environment minor is pinned here; a wrong minor must fail LOUD (not silently at
some later import). The exact interpreter patch is pinned in requirements.lock; this guard checks
the *minor* only (e.g. 3.14.x) so a stranger's point release does not trip it spuriously.
"""

import sys

EXPECTED_PYTHON_MINOR = (3, 14)


def assert_supported_python(actual=None, expected=EXPECTED_PYTHON_MINOR):
    """Raise RuntimeError if the running (or supplied) interpreter minor != the pinned minor.

    Checks the minor only (e.g. 3.14) — the exact patch is pinned in requirements.lock, but a
    stranger's point release (3.14.x) must not trip this. `actual` is an injection seam for tests.
    """
    if actual is None:
        actual = sys.version_info[:2]
    actual = tuple(actual[:2])
    expected = tuple(expected[:2])
    if actual != expected:
        raise RuntimeError(
            f"tracklet requires Python {expected[0]}.{expected[1]}.x (the validated env); "
            f"running {actual[0]}.{actual[1]}. Recreate the venv: `make setup`."
        )
