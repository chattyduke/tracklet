"""S0 AC-0.2 (runtime version guard): a wrong Python minor must fail loud.

The `actual` injection seam lets us prove the guard without spawning a wrong interpreter.
"""
import pytest

from tracklet import _env


def test_expected_minor_is_pinned():
    assert _env.EXPECTED_PYTHON_MINOR == (3, 14)


def test_running_interpreter_passes_by_default():
    # The validated env IS 3.14, so the default (running-interpreter) path must not raise.
    _env.assert_supported_python()


def test_correct_minor_does_not_raise():
    _env.assert_supported_python(actual=(3, 14))


def test_wrong_minor_raises_loud():
    with pytest.raises(RuntimeError):
        _env.assert_supported_python(actual=(3, 11))
