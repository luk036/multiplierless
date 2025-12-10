"""
Spectral Factorization Code

This code implements spectral factorization, which is a mathematical technique used in signal processing. The main purpose of this code is to compute a minimum-phase impulse response that satisfies a given auto-correlation. In simpler terms, it's trying to find a special sequence of numbers (the impulse response) that, when processed in a certain way, matches a given pattern of relationships between data points (the auto-correlation).

The code contains two main functions: spectral_fact and inverse_spectral_fact.

The spectral_fact function takes one input: r, which is the top-half of the auto-correlation coefficients. This input should be a list or array of numbers. The function outputs h, which is the impulse response that gives the desired auto-correlation.

To achieve its purpose, the spectral_fact function follows these steps:

1. It determines the length of the input and creates an oversampled version of it.
2. It computes a logarithmic representation of the input in the frequency domain.
3. It applies a mathematical operation called the Hilbert transform.
4. It combines the results of steps 2 and 3 to create a complex representation.
5. Finally, it converts this representation back to the time domain to get the impulse response.

The function uses several mathematical operations like Fourier transforms, logarithms, and complex number manipulations to achieve this. These operations help transform the data between different representations (time domain and frequency domain) and extract the necessary information to compute the impulse response.

The inverse_spectral_fact function does the opposite of spectral_fact. It takes the impulse response h as input and attempts to reconstruct the original auto-correlation coefficients. This function is simpler and uses a mathematical operation called convolution to compute its result.

Overall, this code provides tools for working with signal processing problems, particularly those involving auto-correlations and impulse responses. It's useful in fields like audio processing, communications, and data analysis where understanding the relationships between data points over time is important.

Spectral Factorization Process Diagram::

    ```svgbob
           Auto-correlation
                 |
                 v
        +-------------------+
        |  Oversampling     |
        +-------------------+
                 |
                 v
        +-------------------+
        | Log computation   |
        |  alpha(w) = 1/2*  |
        |  ln(R(w))         |
        +-------------------+
                 |
                 v
        +-------------------+
        | Hilbert Transform |
        |  phi(w) = H[alpha]|
        +-------------------+
                 |
                 v
        +-------------------+
        | Complex Rep.      |
        |  H(exp(jTw)) =    |
        |  alpha(w) + j*phi |
        +-------------------+
                 |
                 v
        +-------------------+
        | Inverse FFT       |
        |  (Time Domain)    |
        +-------------------+
                 |
                 v
         Impulse Response
    ```

"""

import numpy as np


def spectral_fact(r: np.ndarray) -> np.ndarray:
    """Computes the minimum-phase impulse response which satisfies a given auto-correlation.

    This function implements the Kolmogorov 1939 approach to spectral factorization, as described in pp. 232-233 of "Signal Analysis" by A. Papoulis.

    Args:
        r (numpy.ndarray): The top-half of the auto-correlation coefficients, starting from the 0th element to the end of the auto-correlation. This should be passed in as a column vector.

    Returns:
        numpy.ndarray: The impulse response that gives the desired auto-correlation.

    Examples:
        >>> r = np.array([1.0, 0.5, 0.2])
        >>> h = spectral_fact(r.reshape(-1, 1))
        >>> isinstance(h, np.ndarray)
        True
        >>> h.shape == (r.shape[0], r.shape[0])
        True
    """

    # length of the impulse response sequence
    n = len(r)

    # over-sampling factor
    mult_factor = 100  # should have mult_factor*(n) >> n
    m = mult_factor * n

    # computation method:
    # H(exp(jTw)) = alpha(w) + j*phi(w)
    # where alpha(w) = 1/2*ln(R(w)) and phi(w) = Hilbert_trans(alpha(w))

    # compute 1/2*ln(R(w))
    # w = 2*pi*[0:m-1]/m
    w = np.linspace(0, 2 * np.pi, m, endpoint=False)
    # R = [ones(m, 1) 2*cos(kron(w', [1:n-1]))]*r
    Bn = np.outer(w, np.arange(1, n))
    An = 2 * np.cos(Bn)
    R = np.hstack((np.ones((m, 1)), An)) @ r  # NOQA

    # alpha = ne.evaluate("0.5 * log(abs(R))")
    alpha = 0.5 * np.log(np.abs(R))

    # find the Hilbert transform
    alphatmp = np.fft.fft(alpha)
    # alphatmp(floor(m/2)+1: m) = -alphatmp(floor(m/2)+1: m)
    ind = int(m / 2)  # python3 need int()
    alphatmp[ind:m] = -alphatmp[ind:m]
    alphatmp[0] = 0
    alphatmp[ind] = 0
    phi = np.real(np.fft.ifft(1j * alphatmp))

    # now retrieve the original sampling
    # index = find(np.reminder([0:m-1], mult_factor) == 0)
    index = np.arange(0, m, step=int(mult_factor))
    alpha1 = alpha[index]
    phi1 = phi[index]

    # compute the impulse response (inverse Fourier transform)
    h = np.real(np.fft.ifft(np.exp(alpha1 + 1j * phi1), n))

    return h


def inverse_spectral_fact(h: np.ndarray) -> np.ndarray:
    """
    Computes the auto-correlation sequence from the given impulse response.

    Arguments:
        h (numpy.ndarray): The impulse response sequence.

    Returns:
        numpy.ndarray: The auto-correlation sequence, where the length is the same as the input impulse response.

    Examples:
        >>> h = np.array([1.0, 0.5, 0.2])
        >>> r = inverse_spectral_fact(h)
        >>> isinstance(r, np.ndarray)
        True
        >>> r.shape == (len(h),)
        True
    """
    n = len(h)
    # Take bottom-half of the auto-corelation function due to symmetry ???
    return np.convolve(h, h[::-1])[n - 1 :]
    # r = np.zeros(n)
    # for t in range(n):
    #     r[t] = h[t:] @ h[: n - t]
    # return r


# if __name__ == "__main__":
#     r = np.random.rand(20)
#     h = spectral_fact(r)
#     print(h)
