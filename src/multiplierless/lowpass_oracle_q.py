"""
Lowpass Oracle Q

This code defines a class called LowpassOracleQ, which helps design
multiplierless lowpass filters. A lowpass filter allows low-frequency
signals to pass through while reducing or blocking high-frequency
signals. The "multiplierless" aspect means the filter works without
multiplication operations.

The LowpassOracleQ class takes two inputs: 'nnz' (number of non-zero
elements) and 'lowpass' (another object related to lowpass filter
design).

The main functionality is the 'assess_optim_q' method. It evaluates
and optimizes the filter design by checking feasibility, converting to
CSD representation, and calling the lowpass object's optimization
method.

The code uses spectral factorization, inverse spectral
factorization, and CSD (Canonical Signed Digit) representation.
"""

from typing import Any, Optional, Tuple, Union

import numpy as np
from csdigit.csd import to_csdnnz, to_decimal

from .spectral_fact import inverse_spectral_fact, spectral_fact

__all__ = ["LowpassOracleQ"]

#: Type alias for array-like values or floats used in filter coefficient representation.
Arr = Union[np.ndarray, float]

#: Type alias for a cutting plane, represented as a tuple of (gradient, intercept).
Cut = Tuple[Arr, float]


class LowpassOracleQ:
    """Oracle for multiplierless lowpass filter design with CSD constraints.

    This oracle integrates spectral factorization with Canonical Signed Digit
    (CSD) representation to enable optimization of FIR filter coefficients
    while constraining the number of non-zero CSD digits. It is used in
    ellipsoid method optimization to iteratively refine filter designs.

    The oracle assesses feasibility and optimizes filter coefficients by:
    1. Converting coefficients to minimum-phase impulse response
    2. Converting to CSD representation with the specified constraint
    3. Computing the inverse spectral factorization
    4. Using cutting planes to guide optimization
    """

    def __init__(self, nnz: int, lowpass: Any) -> None:
        """Initializes the LowpassOracleQ object.

        Args:
            nnz (int): Number of non-zero elements in CSD representation.
            lowpass (object): Lowpass filter with assess_feas and assess_optim.
        """
        self.nnz = nnz
        self.lowpass = lowpass
        self.rcsd = np.array([0])
        self.num_retries = 0

    def assess_optim_q(
        self, r: Arr, Spsq: float, retry: bool
    ) -> Tuple[Cut, Arr, Optional[float], bool]:
        """Assesses and optimizes the lowpass filter design with CSD constraints.

        Args:
            r (Arr): Filter coefficients.
            Spsq (float): Frequency response value.
            retry (bool): Whether this is a retry attempt.

        Returns:
            Tuple: (cut, rcsd, Spsq2, can_retry) containing optimized
            coefficients, CSD representation, updated response, and retry flag.
        """
        if not retry:  # retry due to no effect in the previous cut
            self.lowpass.spsq = Spsq
            if cut := self.lowpass.assess_feas(r):
                return cut, r, None, True
            r_array = np.array([r]) if isinstance(r, float) else r
            h = spectral_fact(r_array)
            hcsd = np.array([to_decimal(to_csdnnz(hi, self.nnz)) for hi in h])
            self.rcsd = inverse_spectral_fact(hcsd)
            self.num_retries = 0
        else:
            self.num_retries += 1

        (gc, hc), Spsq2 = self.lowpass.assess_optim(self.rcsd, Spsq)
        hc += gc.dot(self.rcsd - r)
        return (
            (gc, hc),
            self.rcsd,
            Spsq2,
            self.num_retries < self.lowpass.spectrum.shape[0],
        )
