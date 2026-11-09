"""Spectral factorization — FFT (default) and Aberth-Ehrlich root paths."""

from enum import Enum

import numpy as np
from ginger.aberth import aberth_autocorr, initial_aberth_autocorr, poly_from_roots
from ginger.rootfinding import Options

__all__ = [
    "SpectralMethod",
    "spectral_fact",
    "spectral_fact_fft",
    "spectral_fact_root",
    "inverse_spectral_fact",
]

_OVERSAMPLE = 100


def _as_autocorr(r: np.ndarray) -> np.ndarray:
    """Validate and normalize auto-correlation coefficients."""
    arr = np.asarray(r, dtype=float)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError("autocorrelation must be a non-empty 1-D array")
    if not np.all(np.isfinite(arr)):
        raise ValueError("autocorrelation must contain only finite values")
    if arr[0] <= 0:
        raise ValueError("autocorrelation r[0] must be positive")
    return arr


class SpectralMethod(Enum):
    """Spectral factorization method selector (Strategy pattern)."""

    FFT = "fft"
    ROOT = "root"


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
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    r = _as_autocorr(r)
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


def spectral_fact_select(
    r: np.ndarray, method: str | SpectralMethod, tolerance: float = 1e-8
) -> np.ndarray:
    """Spectral factorization with explicit method selection.

    Args:
        r: Auto-correlation coefficients.
        method: Method name (``"fft"``/``"root"``) or :class:`SpectralMethod`.
        tolerance: Root-solver tolerance (used by the ``root`` method).

    Returns:
        Minimum-phase impulse response coefficients.
    """
    m = SpectralMethod(method) if isinstance(method, str) else method
    if m is SpectralMethod.ROOT:
        return spectral_fact_root(r, tolerance)
    return spectral_fact_fft(r)


def _power_spectrum_fft(r: np.ndarray) -> np.ndarray:
    """Compute power spectrum via rfft (matches C++ / Rust approach).

    Zero-pads the autocorrelation sequence to length *m*, takes ``rfft``,
    then returns ``R[k] = 2 · Re(S[k]) - r₀``.
    """
    n = len(r)
    m = _OVERSAMPLE * n
    pad = np.zeros(m)
    pad[:n] = r
    S = np.fft.rfft(pad)
    r0 = float(r[0])
    half = m // 2
    R = np.empty(m)
    R[: half + 1] = 2.0 * S.real - r0
    R[half + 1 :] = R[1 : m - half][::-1]
    return R


def spectral_fact_fft(r: np.ndarray) -> np.ndarray:
    """Kolmogorov 1939 via FFT — rfft-based power spectrum (faster)."""
    r = _as_autocorr(r)
    n = len(r)
    m = _OVERSAMPLE * n
    r0 = float(r[0])

    # FFT-based power spectrum (O(m log m) instead of O(m·n))
    R = _power_spectrum_fft(r)

    scale = max(float(np.max(np.abs(R))), r0)
    min_val = float(np.min(R))
    if min_val <= 0:
        if min_val > -1e-4 * scale:
            R = np.maximum(R, 1e-10 * scale)
        else:
            raise RuntimeError(f"Spectral factorization failed: min={min_val:.6e}")

    alpha = 0.5 * np.log(np.abs(R))
    alphatmp = np.fft.fft(alpha)
    ind = int(m / 2)
    alphatmp[ind:m] = -alphatmp[ind:m]
    alphatmp[0] = 0
    alphatmp[ind] = 0
    phi = np.real(np.fft.ifft(1j * alphatmp))

    index = np.arange(0, m, step=_OVERSAMPLE)
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
    h = np.asarray(h, dtype=float)
    if h.ndim != 1 or h.size == 0:
        raise ValueError("h must be a non-empty 1-D array")
    if not np.all(np.isfinite(h)):
        raise ValueError("h must contain only finite values")
    return np.convolve(h, h[::-1])[len(h) - 1 :]
