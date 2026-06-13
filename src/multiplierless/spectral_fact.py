"""Spectral Factorization — root-finding (default) + FFT (legacy)."""

import numpy as np
from ginger.aberth import aberth_autocorr, initial_aberth_autocorr, poly_from_roots
from ginger.rootfinding import Options

__all__ = [
    "spectral_fact",
    "spectral_fact_fft",
    "spectral_fact_root",
    "inverse_spectral_fact",
]


def spectral_fact_root(r: np.ndarray, tolerance: float = 1e-8) -> np.ndarray:
    """Spectral factorization via Aberth-Ehrlich root-finding.

    Constructs a symmetric polynomial from the auto-correlation coefficients,
    finds its roots using the Aberth-Ehrlich method, selects roots inside the
    unit circle, and reconstructs the minimum-phase impulse response.

    Args:
        r: Auto-correlation coefficients.
        tolerance: Convergence tolerance for root-finding (default 1e-8).

    Returns:
        Minimum-phase impulse response coefficients.
    """
    n = len(r)
    deg = 2 * n - 2
    coeffs = [0.0] * (deg + 1)
    coeffs[0] = float(r[-1])
    for i in range(n - 1):
        coeffs[i + 1] = 2.0 * float(r[n - 2 - i])
    for i in range(n - 2):
        coeffs[deg - i - 1] = 2.0 * float(r[n - 2 - i])
    coeffs[n - 1] = 2.0 * float(r[0])
    coeffs[deg] = float(r[-1])
    coeffs.reverse()

    opts = Options()
    opts.tolerance = tolerance
    opts.max_iters = 500
    zs = initial_aberth_autocorr(coeffs)
    zs, _, _ = aberth_autocorr(coeffs, zs, opts)

    inside = [z if abs(z) < 1.0 else 1.0 / z for z in zs]
    hc = poly_from_roots(inside)
    energy_h = sum(c * c for c in hc)
    norm = np.sqrt(float(r[0]) / energy_h)
    hc = [c * norm for c in hc]

    h = np.zeros(n)
    for i in range(min(n, len(hc))):
        h[i] = hc[i]
    return h


def spectral_fact(r: np.ndarray) -> np.ndarray:
    """Spectral factorization of auto-correlation coefficients.

    Default entry point; delegates to the FFT-based implementation.

    Args:
        r: Auto-correlation coefficients.

    Returns:
        Minimum-phase impulse response coefficients.
    """
    return spectral_fact_fft(r)


def spectral_fact_fft(r: np.ndarray) -> np.ndarray:
    """Kolmogorov 1939 via FFT (legacy)."""
    n = len(r)
    mult_factor = 100
    m = mult_factor * n

    w = np.linspace(0, 2 * np.pi, m, endpoint=False)
    Bn = np.outer(w, np.arange(1, n))
    An = 2 * np.cos(Bn)
    R = np.hstack((np.ones((m, 1)), An)) @ r

    min_val = np.min(R)
    if min_val <= 0:
        if min_val > -1e-4:
            R = np.maximum(R, 1e-10)
        else:
            raise RuntimeError(f"Spectral factorization failed: min={min_val:.6e}")

    alpha = 0.5 * np.log(np.abs(R))
    alphatmp = np.fft.fft(alpha)
    ind = int(m / 2)
    alphatmp[ind:m] = -alphatmp[ind:m]
    alphatmp[0] = 0
    alphatmp[ind] = 0
    phi = np.real(np.fft.ifft(1j * alphatmp))

    index = np.arange(0, m, step=int(mult_factor))
    return np.real(np.fft.ifft(np.exp(alpha[index] + 1j * phi[index]), n))


def inverse_spectral_fact(h: np.ndarray) -> np.ndarray:
    """Inverse spectral factorization — auto-correlation from impulse response.

    Computes the auto-correlation coefficients of a minimum-phase impulse
    response via convolution.

    Args:
        h: Minimum-phase impulse response coefficients.

    Returns:
        Auto-correlation coefficients.
    """
    return np.convolve(h, h[::-1])[len(h) - 1 :]
