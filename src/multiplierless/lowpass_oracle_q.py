"""Lowpass oracle with CSD quantization for multiplierless FIR filter design."""

from math import ceil, fabs, ldexp, log2
from typing import Optional, Protocol, Tuple

import numpy as np
from ellalgo.ell_typing import OracleOptimQ

from .lowpass_oracle import ParallelCut
from .spectral_fact import inverse_spectral_fact, spectral_fact

__all__ = [
    "LowpassOracleLike",
    "LowpassOracleQ",
    "csd_quantize",
    "csd_quantize_parts",
]


def csd_quantize_parts(num: float, nnz: int) -> tuple[float, list[tuple[int, int]]]:
    """Direct double → (double, CSD digits) quantization.

    Matches C++ ``csd_quantize()`` — uses
    ``ldexp(1.0, ceil(log2(|num| · 1.5)) - 1)``
    and iteratively subtracts powers of two up to *nnz* non-zero digits.

    Returns the quantized value together with the chosen ``(exponent, sign)``
    digits.  The digits sum exactly to the value, so callers can render them
    as a CSD string without re-quantizing (and without the two disagreeing).
    """
    if num == 0.0 or nnz == 0:
        return 0.0, []
    result = 0.0
    parts: list[tuple[int, int]] = []
    exp = int(ceil(log2(fabs(num) * 1.5))) - 1
    while nnz > 0 and fabs(num) > 1e-100:
        bit_val = ldexp(1.0, exp)
        if fabs(1.5 * num) > bit_val:
            sgn = 1 if num > 0 else -1
            result += sgn * bit_val
            parts.append((exp, sgn))
            num -= sgn * bit_val
            nnz -= 1
        exp -= 1
    return result, parts


def csd_quantize(num: float, nnz: int) -> float:
    """Direct double → double CSD quantization (no string round-trip)."""
    return csd_quantize_parts(num, nnz)[0]


class LowpassOracleLike(Protocol):
    """Structural interface required from the wrapped lowpass oracle."""

    spectrum: np.ndarray
    sp_sq: float

    def assess_feas(self, x: np.ndarray) -> Optional[ParallelCut]: ...

    def assess_optim(
        self, xc: np.ndarray, gamma: float
    ) -> Tuple[ParallelCut, Optional[float]]: ...


class LowpassOracleQ(OracleOptimQ[np.ndarray]):
    """Oracle for multiplierless lowpass filter design with CSD constraints.

    This oracle integrates spectral factorization with Canonical Signed Digit
    (CSD) representation to enable optimization of FIR filter coefficients
    while constraining the number of non-zero CSD digits. It is used in
    ellipsoid method optimization to iteratively refine filter designs.
    """

    def __init__(self, nnz: int, lowpass: LowpassOracleLike) -> None:
        self.nnz = nnz
        self.lowpass = lowpass
        self.rcsd = np.array([0])
        self._rcsd_valid = False
        self.num_retries = 0
        # Number of frequency grid rows bounds the retry attempts (each retry
        # advances the round-robin scan by one row).
        self.max_retries = self.lowpass.spectrum.shape[0]

    def _csd_point(self, r: np.ndarray) -> np.ndarray:
        """Auto-correlation of the CSD-quantized spectral factor of ``r``."""
        r_array = np.array([r]) if isinstance(r, float) else r
        h = spectral_fact(r_array)
        hcsd = np.array([csd_quantize(float(hi), self.nnz) for hi in h])
        return inverse_spectral_fact(hcsd)

    def assess_optim_q(
        self, r: np.ndarray, Spsq: float, retry: bool
    ) -> Tuple[Tuple[np.ndarray, float], np.ndarray, Optional[float], bool]:
        if not retry:
            if cut := self.lowpass.assess_feas(r):
                return cut, r, None, True
            self.rcsd = self._csd_point(r)
            self._rcsd_valid = True
            self.num_retries = 0
        else:
            self.num_retries += 1
            if not self._rcsd_valid:
                # Feasibility-cut return skipped quantization; compute it now.
                self.rcsd = self._csd_point(r)
                self._rcsd_valid = True

        (gc, hc), Spsq2 = self.lowpass.assess_optim(self.rcsd, Spsq)
        hc += gc.dot(self.rcsd - r)
        return (
            (gc, hc),
            self.rcsd,
            Spsq2,
            self.num_retries < self.max_retries,
        )
