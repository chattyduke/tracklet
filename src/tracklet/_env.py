"""Runtime Python-version guard.

The validated environment minor is pinned here; a wrong minor must fail LOUD (not silently at
some later import). The exact interpreter patch is pinned in requirements.lock; this guard checks
the *minor* only (e.g. 3.14.x) so a stranger's point release does not trip it spuriously.
"""

import sys

EXPECTED_PYTHON_MINOR = (3, 14)


def assert_supported_python(actual=None, expected=EXPECTED_PYTHON_MINOR):
    # STUB (S0): the real loud-failure check is implemented in the green step.
    return None
