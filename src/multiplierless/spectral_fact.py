"""
Spectral Factorization Code

This code implements spectral factorization, a technique used in
signal processing to compute a minimum-phase impulse response that
satisfies a given auto-correlation.

The code contains two functions: spectral_fact and inverse_spectral_fact.

The spectral_fact function takes auto-correlation coefficients as
input and outputs the impulse response.

To achieve its purpose, spectral_fact:
1. Determines length and creates oversampled version
2. Computes logarithmic representation in frequency domain
3. Applies Hilbert transform
4. Creates complex representation
5. Converts back to time domain

The function uses Fourier transforms, logarithms, and complex operations.

The inverse_spectral_fact function does the opposite - takes
impulse response and reconstructs auto-correlation using
convolution.

Overall, this code provides tools for signal processing
problems involving auto-correlations and impulse responses.
"""

import numpy as np

__all__ = ["spectral_fact", "inverse_spectral_fact"]


def spectral_fact(r: np.ndarray) -> np.ndarray:
    """Computes minimum-phase impulse response for given auto-correlation.

    This function implements the Kolmogorov 1939 approach to spectral
    factorization, as described in "Signal Analysis" by A. Papoulis.

    Args:
        r: The top-half of auto-correlation coefficients.

    Returns:
        The impulse response that gives the desired auto-correlation.

    Raises:
        ValueError: If input array is empty or contains invalid values.
        RuntimeError: If numerical errors occur during spectral factorization.
    """
    try:
        if len(r) == 0:
            raise ValueError("Input array cannot be empty")

        if not np.all(np.isfinite(r)):
            raise ValueError("Input array contains non-finite values")

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
                raise RuntimeError(
                    f"Spectral factorization failed: freq response has "
                    f"non-positive values. Min: {min_val:.6e}"
                )

        alpha = 0.5 * np.log(np.abs(R))

        alphatmp = np.fft.fft(alpha)
        ind = int(m / 2)
        alphatmp[ind:m] = -alphatmp[ind:m]
        alphatmp[0] = 0
        alphatmp[ind] = 0
        phi = np.real(np.fft.ifft(1j * alphatmp))

        index = np.arange(0, m, step=int(mult_factor))
        alpha1 = alpha[index]
        phi1 = phi[index]

        h = np.real(np.fft.ifft(np.exp(alpha1 + 1j * phi1), n))

        return h

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid input for spectral factorization: {e}")
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"Linear algebra error: {e}")
    except Exception as e:
        raise RuntimeError(f"Spectral factorization failed: {e}")


def inverse_spectral_fact(h: np.ndarray) -> np.ndarray:
    """Computes auto-correlation sequence from impulse response.

    Args:
        h: The impulse response sequence.

    Returns:
        The auto-correlation sequence.
    """
    n = len(h)
    return np.convolve(h, h[::-1])[n - 1 :]
