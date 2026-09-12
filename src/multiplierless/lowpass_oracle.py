"""Lowpass filter design oracle via spectral factorization.

This module implements the FIR lowpass design oracle used by the
multiplierless CLI. It is the parameterized equivalent of
``ellalgo.oracles.lowpass_oracle.LowpassOracle``, additionally taking a
``discretization_factor`` so the frequency grid density can be tuned.

Constraint evaluation is vectorized: the squared-magnitude response of every
grid row is computed with a single matrix-vector product and the constraints
are tested with boolean masks, preserving the original round-robin cut
selection.
"""

from math import floor
from typing import Any, Optional, Tuple

import numpy as np
from ellalgo.round_robin import RoundRobin

Arr = np.ndarray
ParallelCut = Tuple[Arr, Any]


def _peek(rr: RoundRobin, lo: int, hi: int) -> int:
    """Return the index the next :meth:`RoundRobin.next` call would yield.

    Reads the cursor without advancing it. ``RoundRobin`` exposes no public
    getter, so its cursor slot is read directly.
    """
    nxt = rr._cur + 1
    return lo if nxt >= hi else nxt


def _first_true_cyclic(mask: Arr, start: int, lo: int, size: int) -> int:
    """First ``True`` entry of ``mask`` scanning cyclically from ``start``.

    ``mask`` covers the half-open segment ``[lo, lo + size)``. Returns the
    absolute row index, or ``-1`` when no entry is ``True``.
    """
    if not mask.any():
        return -1
    off = start - lo
    tail = mask[off:]
    if tail.any():
        return lo + off + int(np.argmax(tail))
    return lo + int(np.argmax(mask[:off]))


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
        mdim = self._mdim
        nwpass = self.nwpass
        nwstop = self.nwstop

        # Single BLAS matvec: R(omega) for every grid row at once.
        v = self.spectrum @ x

        # Passband constraints: lp_sq <= v <= up_sq
        if nwpass > 0:
            seg = v[:nwpass]
            mask = (seg > self.up_sq) | (seg < self.lp_sq)
            k = _first_true_cyclic(mask, _peek(self.idx1, 0, nwpass), 0, nwpass)
            if k >= 0:
                self.idx1._cur = k
                vk = v[k]
                if vk > self.up_sq:
                    return self.spectrum[k], (vk - self.up_sq, vk - self.lp_sq)
                return -self.spectrum[k], (self.lp_sq - vk, self.up_sq - vk)

        self.fmax = float("-inf")
        self.kmax = 0
        # Stopband constraint: 0 <= v <= sp_sq, tracking the maximum
        if mdim > nwstop:
            size = mdim - nwstop
            seg = v[nwstop:mdim]
            mask = (seg > self.sp_sq) | (seg < 0.0)
            start = _peek(self.idx3, nwstop, mdim)
            k = _first_true_cyclic(mask, start, nwstop, size)
            if k >= 0:
                self.idx3._cur = k
                vk = v[k]
                if vk > self.sp_sq:
                    return self.spectrum[k], (vk - self.sp_sq, vk)
                return -self.spectrum[k], (-vk, self.sp_sq - vk)
            # No violation: record the maximum response. The value is
            # order-independent, but keep the original cyclic-order
            # tie-breaking for the row index used as the gradient.
            self.fmax = float(seg.max())
            cand = np.flatnonzero(seg == self.fmax)
            if cand.size:
                off = start - nwstop
                after = cand[cand >= off]
                self.kmax = nwstop + int(after[0] if after.size else cand[0])

        # Transition band: only non-negativity
        if nwstop > nwpass:
            size = nwstop - nwpass
            seg = v[nwpass:nwstop]
            mask = seg < 0.0
            k = _first_true_cyclic(mask, _peek(self.idx2, nwpass, nwstop), nwpass, size)
            if k >= 0:
                self.idx2._cur = k
                return -self.spectrum[k], -v[k]

        # First coefficient must be non-negative
        if x[0] < 0:
            self._grad_buf[0] = -1.0
            return self._grad_buf.copy(), -x[0]
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
