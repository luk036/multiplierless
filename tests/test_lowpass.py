import numpy as np
from ellalgo.cutting_plane import Options, cutting_plane_optim, cutting_plane_optim_q
from ellalgo.ell import Ell
from ellalgo.oracles.lowpass_oracle import create_lowpass_case

from multiplierless.lowpass_oracle_q import LowpassOracleQ

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

# rand('twister',sum(100*clock))
# randn('state',sum(100*clock))

# *********************************************************************
# filter specs (for a low-pass filter)
# *********************************************************************
# number of FIR coefficients (including zeroth)


def create_lowpass_q_case(N: int = 48, nnz: int = 8) -> tuple[LowpassOracleQ, float]:
    """Create a CSD-quantized lowpass oracle and its initial stopband bound."""
    omega = create_lowpass_case(N)
    Spsq = omega.sp_sq
    Pcsd = LowpassOracleQ(nnz, omega)
    return Pcsd, Spsq


def run_lowpass() -> tuple[int, bool, bool]:
    N = 32

    r0 = np.zeros(N)
    ellip = Ell(4.0, r0)
    omega = create_lowpass_case(N)
    Spsq = omega.sp_sq
    options = Options()
    options.max_iters = 50000
    options.tolerance = 1e-14
    h, gamma, num_iters = cutting_plane_optim(  # type: ignore
        omega, ellip, Spsq, options
    )
    return num_iters, h is not None, 0.0 < gamma < Spsq


# def test_no_parallel_cut(benchmark) -> None:
#     result, feasible = benchmark(run_lowpass, False)
#     assert feasible
#     assert result >= 13334

# def test_w_parallel_cut(benchmark) -> None:
#     result, feasible = benchmark(run_lowpass, True)
#     assert feasible
#     assert result <= 568


def test_lowpass() -> None:
    result, feasible, improved = run_lowpass()

    assert feasible
    assert improved
    assert 0 < result < 50000


def run_lowpass_q() -> tuple[int, bool, bool]:
    N = 32
    nnz = 7

    r0 = np.zeros(N)
    ellip = Ell(4.0, r0)
    Pcsd, Spsq = create_lowpass_q_case(N, nnz)
    options = Options()
    options.max_iters = 20000
    options.tolerance = 1e-14

    h, gamma, num_iters = cutting_plane_optim_q(  # type: ignore
        Pcsd, ellip, Spsq, options
    )
    return num_iters, h is not None, 0.0 < gamma < Spsq


def test_lowpass_q() -> None:
    result, feasible, improved = run_lowpass_q()

    assert feasible
    assert improved
    assert 0 < result < 20000
