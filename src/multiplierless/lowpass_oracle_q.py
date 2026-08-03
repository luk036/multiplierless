"""Lowpass oracle with CSD quantization for multiplierless FIR filter design."""

from math import ceil, fabs, ldexp, log2
from typing import Any, Optional, Tuple

import numpy as np
from ellalgo.ell_typing import OracleOptimQ

from .spectral_fact import inverse_spectral_fact, spectral_fact

__all__ = ["LowpassOracleQ", "csd_quantize"]


def csd_quantize(num: float, nnz: int) -> float:
    """Direct double → double CSD quantization (no string round-trip).

    Matches C++ `csd_quantize()` — uses
    ``ldexp(1.0, ceil(log2(|num| · 1.5)) - 1)``
    and iteratively subtracts powers of two up to *nnz* non-zero digits.
    """
    if num == 0.0 or nnz == 0:
        return 0.0
    result = 0.0
    bit_val = ldexp(1.0, int(ceil(log2(fabs(num) * 1.5))) - 1)
    while nnz > 0 and fabs(num) > 1e-100:
        if fabs(1.5 * num) > bit_val:
            sgn = 1.0 if num > 0 else -1.0
            result += sgn * bit_val
            num -= sgn * bit_val
            nnz -= 1
        bit_val *= 0.5
    return result


class LowpassOracleQ(OracleOptimQ[np.ndarray]):
    """Oracle for multiplierless lowpass filter design with CSD constraints.

    This oracle integrates spectral factorization with Canonical Signed Digit
    (CSD) representation to enable optimization of FIR filter coefficients
    while constraining the number of non-zero CSD digits. It is used in
    ellipsoid method optimization to iteratively refine filter designs.
    """

    def __init__(self, nnz: int, lowpass: Any) -> None:
        self.nnz = nnz
        self.lowpass = lowpass
        self.rcsd = np.array([0])
        self.num_retries = 0

    def assess_optim_q(
        self, r: np.ndarray, Spsq: float, retry: bool
    ) -> Tuple[Tuple[np.ndarray, float], np.ndarray, Optional[float], bool]:
        if not retry:
            self.lowpass.spsq = Spsq
            if cut := self.lowpass.assess_feas(r):
                return cut, r, None, True
            r_array = np.array([r]) if isinstance(r, float) else r
            h = spectral_fact(r_array)
            hcsd = np.array([csd_quantize(float(hi), self.nnz) for hi in h])
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
