import subprocess
import sys


def test_version_unknown_on_package_not_found():
    """When the package metadata is unavailable, __version__ should be 'unknown'.

    Runs in a subprocess to get a clean import environment.
    """
    code = """
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError
with patch("importlib.metadata.version", side_effect=PackageNotFoundError("multiplierless")):
    import importlib
    import sys
    if "multiplierless" in sys.modules:
        del sys.modules["multiplierless"]
    from multiplierless import __version__
    assert __version__ == "unknown", f"Expected 'unknown', got {__version__!r}"
    print("OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd="D:\\github\\py\\multiplierless",
    )
    assert result.returncode == 0, f"Subprocess failed: {result.stderr}"


def test_version_is_string():
    """Check that __version__ is a string (basic sanity)."""
    from multiplierless import __version__

    assert isinstance(__version__, str)
