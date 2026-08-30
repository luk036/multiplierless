"""Lowpass filter design oracle via spectral factorization.

This module implements the FIR lowpass design oracle used by the
multiplierless CLI. It is the parameterized equivalent of
``ellalgo.oracles.lowpass_oracle.LowpassOracle``, additionally taking a
``discretization_factor`` so the frequency grid density can be tuned.

The constraint scans share a common Template-Method skeleton
(:func:`_scan_constraints`) and reuse ``ellalgo.round_robin.RoundRobin`` for
the cyclic row iteration, mirroring
``multiplierless/source/lowpass_oracle.cpp``.
"""

from math import floor
from typing import Any, Callable, Optional, Tuple

import numpy as np

from ellalgo.round_robin import RoundRobin

Arr = np.ndarray
ParallelCut = Tuple[Arr, Any]
Check = Callable[[int, Arr, float], Optional[ParallelCut]]


def _scan_constraints(
    rr: RoundRobin, count: int, x: Arr, spectrum: Arr, check: Check
) -> Optional[ParallelCut]:
    """Template-Method skeleton: scan ``count`` rows of ``spectrum`` in
    round-robin order and return the first violating cut reported by
    ``check``, or None if none of the rows violate.

    Args:
        rr: Round-robin row iterator.
        count: Number of rows to scan.
        x: The variable vector (autocorrelation coefficients).
        spectrum: The pre-computed cosine spectrum matrix.
        check: Callback ``check(row, col_k, v) -> Optional[ParallelCut]``.

    Returns:
        The first violating cut, or None.
    """
    for _ in range(count):
        k = rr.next()
        col_k = spectrum[k]
        v = col_k.dot(x)
        if cut := check(k, col_k, v):
            return cut
    return None


class LowpassOracle:
    """Oracle for the FIR lowpass filter design problem.

    Evaluates the squared-magnitude frequency response :math:`R(\\omega)` of
    the candidate autocorrelation coefficients against passband/stopband
    bounds, returning a cutting plane when a constraint is violated.
    """

    def __init__(
        self,
        N: int,
        wpass: float,
        wstop: float,
        delta0_wpass: float,
        delta0_wstop: float,
        discretization_factor: int,
    ) -> None:
        """Build the oracle with fully parameterized filter specs.

        Args:
            N: Filter order (number of FIR coefficients).
            wpass: Normalized passband edge (×π rad/sample).
            wstop: Normalized stopband edge (×π rad/sample).
            delta0_wpass: Passband ripple (linear).
            delta0_wstop: Stopband attenuation (linear).
            discretization_factor: Grid density multiplier (m = factor × N).
        """
        mdim = discretization_factor * N
        w = np.linspace(0, np.pi, mdim)
        temp = 2 * np.cos(np.outer(w, np.arange(1, N)))
        self.spectrum = np.concatenate((np.ones((mdim, 1)), temp), axis=1)

        self.nwpass = floor(wpass * np.pi * (mdim - 1) / np.pi) + 1
        self.nwstop = floor(wstop * np.pi * (mdim - 1) / np.pi) + 1

        delta1 = 20 * np.log10(1 + delta0_wpass)
        delta2 = 20 * np.log10(delta0_wstop)

        low_pass = pow(10, -delta1 / 20)
        up_pass = pow(10, +delta1 / 20)
        stop_pass = pow(10, +delta2 / 20)

        self.lp_sq = low_pass * low_pass
        self.up_sq = up_pass * up_pass
        self.sp_sq = stop_pass * stop_pass

        self.idx1 = RoundRobin(self.nwpass)  # passband scan: [0, nwpass)
        # transition band scan: [nwpass, nwstop)
        self.idx2 = RoundRobin(self.nwstop, lo=self.nwpass)
        self.idx3 = RoundRobin(mdim, lo=self.nwstop)  # stopband: [nwstop, mdim)
        self.fmax = float("-inf")
        self.kmax = 0
        self._mdim = mdim
        self._ndim = N
        # Pre-allocated gradient buffer (avoids np.zeros in hot path)
        self._grad_buf = np.zeros(N)

    def assess_feas(self, x: np.ndarray) -> Optional[ParallelCut]:
        """Check whether the coefficients meet the filter design specs.

        Args:
            x: The filter coefficients (autocorrelation coefficients).

        Returns:
            A parallel cut (gradient, objective) when a constraint is
            violated, or None when the point is feasible.
        """
        mdim, ndim = self.spectrum.shape

        # Passband constraints: lp_sq <= v <= up_sq
        if cut := _scan_constraints(
            self.idx1, self.nwpass, x, self.spectrum, self._check_passband
        ):
            return cut

        self.fmax = float("-inf")
        self.kmax = 0
        # Stopband constraint: 0 <= v <= sp_sq, tracking the maximum
        if cut := _scan_constraints(
            self.idx3, mdim - self.nwstop, x, self.spectrum, self._check_stopband
        ):
            return cut

        # Transition band: only non-negativity
        if cut := _scan_constraints(
            self.idx2, self.nwstop - self.nwpass, x, self.spectrum, self._check_nonneg
        ):
            return cut

        # First coefficient must be non-negative
        if x[0] < 0:
            self._grad_buf[0] = -1.0
            return self._grad_buf.copy(), -x[0]
        return None

    def _check_passband(self, k: int, col_k: Arr, v: float) -> Optional[ParallelCut]:
        if v > self.up_sq:
            return col_k, (v - self.up_sq, v - self.lp_sq)
        if v < self.lp_sq:
            return -col_k, (-v + self.lp_sq, -v + self.up_sq)
        return None

    def _check_stopband(self, k: int, col_k: Arr, v: float) -> Optional[ParallelCut]:
        if v > self.sp_sq:
            return col_k, (v - self.sp_sq, v)
        if v < 0:
            return -col_k, (-v, -v + self.sp_sq)
        if v > self.fmax:
            self.fmax = v
            self.kmax = k
        return None

    def _check_nonneg(self, k: int, col_k: Arr, v: float) -> Optional[ParallelCut]:
        if v < 0:
            return -col_k, -v
        return None

    def assess_optim(
        self, xc: np.ndarray, gamma: float
    ) -> Tuple[ParallelCut, Optional[float]]:
        """Assess optimality: return the maximum stopband response.

        Args:
            xc: The filter coefficients (autocorrelation coefficients).
            gamma: The current best stopband attenuation value.

        Returns:
            A tuple of (parallel cut, max stopband value), where the value is
            None when the point is infeasible.
        """
        self.sp_sq = gamma
        if cut := self.assess_feas(xc):
            return cut, None
        return (self.spectrum[self.kmax], (0.0, self.fmax)), self.fmax


def create_lowpass_case_params(
    N: int,
    wpass: float,
    wstop: float,
    delta0_wpass: float,
    delta0_wstop: float,
    discretization_factor: int,
) -> LowpassOracle:
    """Build a :class:`LowpassOracle` with fully parameterized filter specs.

    Args:
        N: Filter order (number of FIR coefficients).
        wpass: Normalized passband edge (×π rad/sample).
        wstop: Normalized stopband edge (×π rad/sample).
        delta0_wpass: Passband ripple (linear).
        delta0_wstop: Stopband attenuation (linear).
        discretization_factor: Grid density multiplier (m = factor × N).

    Returns:
        A configured LowpassOracle.
    """
    return LowpassOracle(
        N, wpass, wstop, delta0_wpass, delta0_wstop, discretization_factor
    )
