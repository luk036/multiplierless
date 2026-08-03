"""Spectral factorization of an auto-correlation sequence via FFT + Hilbert transform."""










import matplotlib.pyplot as plt
import numpy as np


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
    h = np.fft.ifft(np.exp(alpha1 + 1j * phi1))
    h = np.real(h[:nr])
    return h
