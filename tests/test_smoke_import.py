"""S0 smoke: the package imports and exposes its version."""
import tracklet


def test_package_imports_and_has_version():
    assert tracklet.__version__ == "0.1.2"
