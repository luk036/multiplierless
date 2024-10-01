"""
Lowpass Oracle Q

This code defines a class called LowpassOracleQ, which is designed to help with the problem of designing multiplierless lowpass filters. A lowpass filter is a type of signal processing tool that allows low-frequency signals to pass through while reducing or blocking high-frequency signals. The "multiplierless" aspect means the filter is designed to work without using multiplication operations, which can be beneficial in certain hardware implementations.

The LowpassOracleQ class takes two inputs when initialized: 'nnz' (which likely stands for "number of non-zero elements") and 'lowpass' (which is probably another object related to lowpass filter design). These inputs are stored as attributes of the class for later use.

The main functionality of this class is provided by the 'assess_optim_q' method. This method takes three inputs: 'r' (an array of numbers), 'Spsq' (likely related to the filter's frequency response), and 'retry' (a boolean indicating whether this is a retry attempt).

The purpose of the 'assess_optim_q' method is to evaluate and optimize the filter design. It does this through a series of steps:

1. If it's not a retry, it first checks if the current design is feasible using the 'assess_feas' method of the 'lowpass' object.
2. If feasible, it converts the input 'r' into a filter response using spectral factorization, then converts this to a CSD (Canonical Signed Digit) representation, which is a way of representing numbers that's useful for multiplierless designs.
3. If it's a retry, or after the above steps, it calls the 'assess_optim' method of the 'lowpass' object to further optimize the design.
4. Finally, it returns a tuple containing the optimized filter coefficients, the CSD representation of the filter, an updated frequency response, and a boolean indicating whether further retries are possible.

The code uses several mathematical operations and transformations, including spectral factorization and its inverse, which are advanced concepts in signal processing. It also uses the CSD number representation, which is a special way of representing numbers that's useful in digital filter design.

The output of this code is not a final filter design, but rather an intermediate step in an iterative optimization process. It provides updated filter coefficients and frequency response characteristics that can be used in further iterations of the design process.

This code is part of a larger system for designing digital filters, specifically tailored for situations where multiplication operations need to be avoided. It's a specialized tool that would be used by engineers or researchers working on digital signal processing systems with specific hardware constraints.
"""

from __future__ import print_function

from typing import Tuple, Union

import numpy as np

from csdigit.csd import to_csdnnz, to_decimal
from .spectral_fact import inverse_spectral_fact, spectral_fact

Arr = Union[np.ndarray, float]
Cut = Tuple[Arr, float]


class LowpassOracleQ:
    """Lowpass oracle for the multiplierless lowpass filter design problem.

    Returns:
        [type]: [description]
    """

    def __init__(self, nnz, lowpass):
        """[summary]

        Arguments:
            nnz ([type]): [description]
            lowpass ([type]): [description]
        """
        self.nnz = nnz
        self.lowpass = lowpass
        self.rcsd = np.array([0])
        self.num_retries = 0

    def assess_optim_q(self, r: Arr, Spsq, retry: bool):
        """[summary]

        Arguments:
            r (Arr): [description]
            Spsq ([type]): [description]
            retry (int): [description]

        Returns:
            [type]: [description]
        """
        if not retry:  # retry due to no effect in the previous cut
            # self.lowpass.retry = False
            self.lowpass.spsq = Spsq
            if cut := self.lowpass.assess_feas(r):
                return cut, r, None, True
            h = spectral_fact(r)
            hcsd = np.array([to_decimal(to_csdnnz(hi, self.nnz)) for hi in h])
            self.rcsd = inverse_spectral_fact(hcsd)
            self.num_retries = 0  # reset to zero
        else:
            # self.lowpass.retry = True
            self.num_retries += 1

        (gc, hc), Spsq2 = self.lowpass.assess_optim(self.rcsd, Spsq)
        hc += gc.dot(self.rcsd - r)
        return (
            (gc, hc),
            self.rcsd,
            Spsq2,
            self.num_retries < self.lowpass.spectrum.shape[0],
        )
