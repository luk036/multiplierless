import numpy as np
import pytest
from pytest import approx

from multiplierless.spectral_fact import (
    inverse_spectral_fact,
    spectral_fact,
    spectral_fact_fft,
    spectral_fact_root,
)


def test_spectral_fact() -> None:
    h = np.array(
        [
            0.76006445,
            0.54101887,
            0.42012073,
            0.3157191,
            0.10665804,
            0.04326203,
            0.01315678,
        ]
    )
    r = inverse_spectral_fact(h)
    h2 = spectral_fact(r)
    assert len(h) == len(h2)
    print(h2)
    assert h2 == approx(h)


def test_spectral_fact_root() -> None:
    """Test spectral_fact_root — the root-based spectral factorization."""
    h = np.array(
        [
            0.76006445,
            0.54101887,
            0.42012073,
            0.3157191,
            0.10665804,
            0.04326203,
            0.01315678,
        ]
    )
    r = inverse_spectral_fact(h)
    h_root = spectral_fact_root(r)

    assert isinstance(h_root, np.ndarray)
    assert len(h_root) == len(h)
    energy_orig = sum(h**2)
    energy_root = sum(h_root**2)
    assert energy_root == approx(energy_orig, abs=1e-2)


def test_spectral_fact_root_with_custom_tolerance() -> None:
    """Test spectral_fact_root with explicit tolerance parameter."""
    h = np.array([0.76006445, 0.54101887, 0.42012073])
    r = inverse_spectral_fact(h)
    h_root = spectral_fact_root(r, tolerance=1e-6)
    assert len(h_root) == len(h)
    energy_orig = sum(h**2)
    energy_root = sum(h_root**2)
    assert energy_root == approx(energy_orig, abs=1e-2)


def test_spectral_fact_root_energy_preserving() -> None:
    """Verify that spectral_fact_root preserves the energy (r[0])."""
    r = np.array([1.16, 0.81, 0.55, 0.32, 0.11, 0.04, 0.01])
    h_root = spectral_fact_root(r)
    energy = sum(h_root**2)
    assert energy == approx(r[0], abs=1e-2)


def test_spectral_fact_fft_runtime_error() -> None:
    """Test that spectral_fact_fft raises RuntimeError with invalid input."""
    # An autocorrelation sequence that produces significantly negative
    # spectrum (small r[0] relative to other lags) triggers the error
    r_bad = np.array([0.01, 0.5, 0.3])
    with pytest.raises(RuntimeError, match="Spectral factorization failed"):
        spectral_fact_fft(r_bad)


def test_spectral_fact_fft_clamps_small_negative() -> None:
    """Test that spectral_fact_fft clamps slightly negative values."""
    # This autocorrelation produces min(R) ≈ -6.7e-5, which is in (-1e-4, 0]
    r = np.array([1.213065, 0.606566, 0.0])
    h = spectral_fact_fft(r)
    assert isinstance(h, np.ndarray)
    assert len(h) == len(r)
