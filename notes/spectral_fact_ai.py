"""
Spectral Factorization Function

This code defines a function called spectral_fact that performs spectral factorization, which is a mathematical technique used in signal processing. The purpose of this function is to find a causal and stable filter from a given autocorrelation sequence.

The function takes one input: r, which is an array representing the autocorrelation sequence of a signal. It processes this input to produce an output h, which is the impulse response of the desired filter.

Here's how the function achieves its purpose:

First, it determines the length of the input sequence and sets up some parameters for oversampling. This oversampling is done to improve the accuracy of the calculations. Then, it computes the power spectral density (PSD) of the input sequence using the Fourier transform.

Next, the function calculates the logarithm of the PSD, which is split into two parts: the magnitude (alpha) and the phase (phi). The phase is computed using the Hilbert transform of the magnitude. This step is crucial because it ensures that the resulting filter will be causal and stable.

After computing these components, the function returns to the original sampling rate by selecting specific indices from the oversampled data. Finally, it combines the magnitude and phase information and applies an inverse Fourier transform to obtain the impulse response of the filter.

The main data transformations happening in this code involve Fourier transforms, logarithmic operations, and the Hilbert transform. These mathematical operations allow the function to move between the time domain (where the autocorrelation sequence lives) and the frequency domain (where the spectral factorization is performed).

It's worth noting that this function uses numpy, a powerful library for numerical computations in Python. Many of the operations, such as the Fourier transforms and array manipulations, are performed using numpy functions, which makes the code more efficient and easier to read.

In summary, this function takes an autocorrelation sequence as input, performs spectral factorization through a series of mathematical transformations, and outputs the impulse response of a causal and stable filter. This type of operation is commonly used in various signal processing applications, such as filter design and signal prediction.
"""

import numpy as np
import matplotlib.pyplot as plt


def spectral_fact(r):
    # length of the impulse response sequence
    nr = len(r)
    n = int((nr + 1) / 2)
    # over-sampling factor
    mult_factor = 30  # should have mult_factor*(n) >> n
    m = mult_factor * n
    # computation method:
    # H(exp(jTw)) = alpha(w) + j*phi(w)
    # where alpha(w) = 1/2*ln(R(w)) and phi(w) = Hilbert_trans(alpha(w))
    # compute 1/2*ln(R(w))
    w = 2 * np.pi * np.arange(m) / m
    R = np.exp(-1j * np.kron(w, np.arange(-(n - 1), n))) * r
    R = np.abs(np.real(R))  # remove numerical noise from the imaginary part
    plt.plot(20 * np.log10(R))
    alpha = 1 / 2 * np.log(R)
    # find the Hilbert transform
    alphatmp = np.fft.fft(alpha)
    alphatmp[np.floor(m / 2).astype(int) + 1 : m] = -alphatmp[
        np.floor(m / 2).astype(int) + 1 : m
    ]
    alphatmp[0] = 0
    alphatmp[np.floor(m / 2).astype(int) + 1] = 0
    phi = np.real(np.fft.ifft(1j * alphatmp))
    # now retrieve the original sampling
    index = np.where(np.remainder(np.arange(m), mult_factor) == 0)[0]
    alpha1 = alpha[index]
    phi1 = phi[index]
    # compute the impulse response (inverse Fourier transform)
    h = np.fft.ifft(np.exp(alpha1 + 1j * phi1), n)
    return h
