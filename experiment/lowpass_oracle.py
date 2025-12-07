"""
Lowpass Oracle

This code implements a LowpassOracle, which is used to design a low-pass filter
for signal processing. A low-pass filter allows low-frequency signals to pass
through while attenuating high-frequency signals. The main purpose of this code
is to help optimize the design of such a filter by providing a way to assess
whether a given set of filter coefficients meets certain specifications.

The code defines a class called LowpassOracle that takes several inputs when initialized:

1. ndim: The number of filter coefficients
2. wpass: The end of the passband (frequencies that should pass through)
3. wstop: The end of the stopband (frequencies that should be attenuated)
4. lp_sq: The lower bound for the squared magnitude response in the passband
5. up_sq: The upper bound for the squared magnitude response in the passband
6. sp_sq: The upper bound for the squared magnitude response in the stopband

The main outputs of this code are produced by two methods: assess_feas and assess_optim. These methods take a set of filter coefficients as input and determine whether they meet the specified requirements or how close they are to meeting them.

The LowpassOracle achieves its purpose through a series of checks on the
frequency response of the filter. It uses a pre-computed spectrum matrix to
efficiently calculate the frequency response at different points. The code then
checks if the response falls within the specified bounds for the passband and
stopband.

The important logic flow in this code involves iterating through different
frequency points and checking the filter's response at each point. If any
violations of the specifications are found, the code returns information about
the violation, which can be used to adjust the filter coefficients.

A key data transformation happening in this code is the conversion from filter coefficients to frequency response. This is done using the pre-computed spectrum matrix, which allows for efficient calculation of the response at many frequency points.

The code also includes a helper function called create_lowpass_case, which sets up a specific instance of the LowpassOracle with predefined parameters. This function can be used to quickly create a standard test case for filter design.

Overall, this code provides a tool for iteratively designing and optimizing
low-pass filters by giving feedback on how well a set of coefficients meets the
desired specifications. It's part of a larger optimization process where the
coefficients would be adjusted based on the feedback from this oracle until a
satisfactory filter design is achieved.
"""

from math import floor
from typing import Optional, Tuple

import numpy as np

from ellalgo.ell_typing import CutChoice, OracleOptim

Arr = np.ndarray
ParallelCut = Tuple[Arr, CutChoice]


# Modified from CVX code by Almir Mutapcic in 2006.
# Adapted in 2010 for impulse response peak-minimization by convex iteration
# by Christine Law.
#
# "FIR Filter Design via Spectral Factorization and Convex Optimization"
# by S.-P. Wu, S. Boyd, and L. Vandenberghe
#
# Designs an FIR lowpass filter using spectral factorization method with
# constraint on maximum passband ripple and stopband attenuation:
#
#   minimize   max |H(w)|                      for w in stopband
#       s.t.   1/delta <= |H(w)| <= delta      for w in passband
#
# We change variables via spectral factorization method and get:
#
#   minimize   max R(w)                          for w in stopband
#       s.t.   (1/delta)**2 <= R(w) <= delta**2  for w in passband
#              R(w) >= 0                         for all w
#
# where R(w) is squared magnitude frequency response
# (and Fourier transform of autocorrelation coefficients r).
# Variables are coeffients r and gra = hh' where h is impulse response.
# delta is allowed passband ripple.
# This is a convex problem (can be formulated as an SDP after sampling).


# *********************************************************************
# filter specs (for a low-pass filter)
# *********************************************************************
# number of FIR coefficients (including zeroth)
class LowpassOracle(OracleOptim):
    # more_alt: bool = True
    idx1: int = 0

    def __init__(
        self,
        ndim: int,
        wpass: float,
        wstop: float,
        lp_sq: float,
        up_sq: float,
        sp_sq: float,
    ):
        """
        Initializes a LowpassOracle object with the given parameters.

        Args:
            ndim (int): The number of FIR coefficients (including the zeroth).
            wpass (float): The end of the passband.
            wstop (float): The end of the stopband.
            lp_sq (float): The lower bound on the squared magnitude frequency response in the passband.
            up_sq (float): The upper bound on the squared magnitude frequency response in the passband.
            sp_sq (float): The upper bound on the squared magnitude frequency response in the stopband.

        Attributes:
            spectrum (np.ndarray): The matrix used to compute the power spectrum.
            nwpass (int): The index of the end of the passband.
            nwstop (int): The index of the end of the stopband.
            lp_sq (float): The lower bound on the squared magnitude frequency response in the passband.
            up_sq (float): The upper bound on the squared magnitude frequency response in the passband.
            sp_sq (float): The upper bound on the squared magnitude frequency response in the stopband.
            idx1 (int): The current index for the passband.
            idx2 (int): The current index for the stopband.
            idx3 (int): The current index for the stopband.
            fmax (float): The maximum value of the squared magnitude frequency response.
            kmax (int): The index of the maximum value of the squared magnitude frequency response.
        """
        # *********************************************************************
        # optimization parameters
        # *********************************************************************
        # rule-of-thumb discretization (from Cheney's Approximation Theory)
        mdim = 15 * ndim  # Number of frequency points to evaluate
        w = np.linspace(0, np.pi, mdim)  # omega (frequency points from 0 to π)

        # spectrum is the matrix used to compute the power spectrum
        # spectrum(w,:) = [1 2*cos(w) 2*cos(2*w) ... 2*cos(mdim*w)]
        # This creates a matrix where each row corresponds to a frequency point,
        # and each column contains the cosine terms for that frequency
        temp = 2 * np.cos(np.outer(w, np.arange(1, ndim)))
        self.spectrum = np.concatenate((np.ones((mdim, 1)), temp), axis=1)

        # Convert normalized frequency bounds to array indices
        self.nwpass: int = floor(wpass * (mdim - 1)) + 1  # end of passband
        self.nwstop: int = floor(wstop * (mdim - 1)) + 1  # end of stopband

        # Store the squared magnitude bounds
        self.lp_sq = lp_sq  # Lower bound for passband (squared)
        self.up_sq = up_sq  # Upper bound for passband (squared)
        self.sp_sq = sp_sq  # Upper bound for stopband (squared)

        # Initialize indices for round-robin checking of frequency points
        self.idx1 = 0  # Current index for passband checking
        self.idx2 = self.nwpass  # Current index for transition band checking
        self.idx3 = self.nwstop  # Current index for stopband checking

        # Variables to track maximum response in stopband
        self.fmax = float("-inf")  # Maximum response value found
        self.kmax = 0  # Index where maximum response occurs

    def assess_feas(self, x: Arr) -> Optional[ParallelCut]:
        """
        Assess whether the given filter coefficients meet the design specifications.

        This method checks the frequency response at various points in three bands:
        1. Passband (0 to nwpass): Checks if response is within [lp_sq, up_sq]
        2. Stopband (nwstop to end): Checks if response is below sp_sq and non-negative
        3. Transition band (nwpass to nwstop): Checks if response is non-negative

        Uses a round-robin approach to check different frequency points on each call
        to distribute the computational load across multiple iterations.

        Args:
            x (Arr): The filter coefficients (autocorrelation coefficients)

        Returns:
            Optional[ParallelCut]:
                - None if all specifications are met
                - A tuple containing:
                    * The gradient of the violating constraint
                    * The violation amount (or tuple of lower/upper violations)
        """
        # Get dimensions of the spectrum matrix
        mdim, ndim = self.spectrum.shape

        # Check passband frequencies (0 to nwpass)
        for _ in range(self.nwpass):
            self.idx1 += 1
            if self.idx1 == self.nwpass:
                self.idx1 = 0  # round robin - wrap around to start

            col_k = self.spectrum[self.idx1, :]  # Get frequency point coefficients
            v = col_k.dot(x)  # Compute response at this frequency

            # Check upper bound violation
            if v > self.up_sq:
                f = (v - self.up_sq, v - self.lp_sq)
                return col_k, f  # Return gradient and violation amounts

            # Check lower bound violation
            if v < self.lp_sq:
                f = (-v + self.lp_sq, -v + self.up_sq)
                return -col_k, f  # Return negative gradient and violation amounts

        # Initialize tracking for stopband maximum response
        self.fmax = float("-inf")
        self.kmax = 0

        # Check stopband frequencies (nwstop to end)
        for _ in range(self.nwstop, mdim):
            self.idx3 += 1
            if self.idx3 == mdim:
                self.idx3 = self.nwstop  # round robin - wrap around to start

            col_k = self.spectrum[self.idx3, :]
            v = col_k.dot(x)

            # Check upper bound violation in stopband
            if v > self.sp_sq:
                return col_k, (v - self.sp_sq, v)

            # Check non-negativity constraint
            if v < 0:
                return -col_k, (-v, -v + self.sp_sq)

            # Track maximum response in stopband (for optimization)
            if v > self.fmax:
                self.fmax = v
                self.kmax = self.idx3

        # Check transition band frequencies (nwpass to nwstop)
        # Only need to ensure non-negativity here
        for _ in range(self.nwpass, self.nwstop):
            self.idx2 += 1
            if self.idx2 == self.nwstop:
                self.idx2 = self.nwpass  # round robin - wrap around to start

            col_k = self.spectrum[self.idx2, :]
            v = col_k.dot(x)

            # Check non-negativity constraint
            if v < 0:
                return -col_k, -v  # Return single cut for non-negativity

        # Additional check: First coefficient should be non-negative
        if x[0] < 0:
            grad = np.zeros(ndim)
            grad[0] = -1.0
            return grad, -x[0]

        # If all checks pass, return None (no violations)
        return None

    def assess_optim(
        self, xc: Arr, gamma: float
    ) -> Tuple[ParallelCut, Optional[float]]:
        """
        Assess the optimality of the current filter coefficients for the stopband.

        First checks feasibility using assess_feas. If feasible, returns information
        about the maximum response in the stopband which can be used to further
        optimize the filter design.

        Args:
            xc (Arr): The filter coefficients (autocorrelation coefficients)
            gamma (float): The current best stopband attenuation value to beat

        Returns:
            tuple: A tuple containing:
                - A tuple of (gradient, (lower, upper)) for the maximum stopband response
                - The maximum stopband response value (or None if not feasible)
        """
        # Update the stopband bound
        self.sp_sq = gamma

        # First check feasibility
        if cut := self.assess_feas(xc):
            return cut, None  # Return feasibility cut and no objective value

        # If feasible, return information about the maximum stopband response
        return (self.spectrum[self.kmax, :], (0.0, self.fmax)), self.fmax


# *********************************************************************
# filter specs (for a low-pass filter)
# *********************************************************************
# number of FIR coefficients (including zeroth)
def create_lowpass_case(ndim: int = 48) -> "LowpassOracle":
    """
    Creates a standard low-pass filter design case with typical parameters.

    Sets up a LowpassOracle instance with commonly used specifications:
    - Passband edge at 0.12π
    - Stopband edge at 0.20π
    - Passband ripple of ±0.025 dB
    - Stopband attenuation of 0.125

    Args:
        ndim (int, optional): Number of filter coefficients. Defaults to 48.

    Returns:
        LowpassOracle: An initialized LowpassOracle instance with standard parameters
    """
    # Define normalized frequency tolerances
    delta0_wpass = 0.025  # Passband ripple tolerance
    delta0_wstop = 0.125  # Stopband attenuation tolerance

    # Convert to dB scale for calculations
    delta1 = 20 * np.log10(1 + delta0_wpass)  # Passband ripple in dB
    delta2 = 20 * np.log10(delta0_wstop)  # Stopband attenuation in dB

    # Convert dB specifications to linear scale
    low_pass = pow(10, -delta1 / 20)  # Lower passband bound
    up_pass = pow(10, +delta1 / 20)  # Upper passband bound
    stop_pass = pow(10, +delta2 / 20)  # Stopband bound

    # Square the bounds for use with squared magnitude response
    lp_sq = low_pass * low_pass
    up_sq = up_pass * up_pass
    sp_sq = stop_pass * stop_pass

    # Create and return LowpassOracle instance with these parameters
    return LowpassOracle(ndim, 0.12, 0.20, lp_sq, up_sq, sp_sq)
