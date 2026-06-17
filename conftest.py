"""pytest session config — fail loud immediately on a wrong Python minor (S0 AC-0.2).

If the interpreter minor != the pinned one, the whole collection errors here rather than failing
mysteriously deep in an astropy/opencv import later.
"""
from tracklet._env import assert_supported_python

assert_supported_python()
